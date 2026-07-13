import logging
from generation.llm import complete_text
from generation.groq import GROQ_BASE_URL, GROQ_QUERY_REWRITE_MODEL, complete_with_groq

RECENT_MESSAGE_LIMIT = 7
SUMMARY_TRIGGER_LIMIT = 9
MAX_MESSAGE_CHARS = 1200


def sanitize_messages(messages):
    clean_messages = []
    for message in messages or []:
        role = message.get("role")
        content = (message.get("content") or "").strip()
        if role not in {"user", "assistant"} or not content:
            continue
        clean_messages.append({
            "role": role,
            "content": content[:MAX_MESSAGE_CHARS]
        })
    return clean_messages


def format_messages(messages):
    return "\n".join(
        f"{message['role'].title()}: {message['content']}"
        for message in messages
    )


def build_memory_context(memory):
    memory = memory or {}
    summary = (memory.get("summary") or "").strip()
    messages = sanitize_messages(memory.get("messages") or [])[-RECENT_MESSAGE_LIMIT:]

    return {
        "summary": summary,
        "messages": messages,
        "recent_messages_text": format_messages(messages),
        "turns_used": len(messages),
        "rewrite_model": GROQ_QUERY_REWRITE_MODEL,
        "rewrite_api": GROQ_BASE_URL
    }


def rewrite_query_with_memory(query, memory_context):
    if not memory_context["summary"] and not memory_context["messages"]:
        return query.strip()

    system_prompt = (
        "Rewrite the latest user question into a standalone search query for a RAG system. "
        "Use the conversation summary and recent turns only to resolve references. "
        "Do not answer the question. Return only the rewritten query."
    )
    user_prompt = f"""
Conversation summary:
{memory_context['summary'] or 'None'}

Recent conversation:
{memory_context['recent_messages_text'] or 'None'}

Latest user question:
{query}
"""

    try:
        rewritten = complete_with_groq(system_prompt, user_prompt)
        return rewritten.strip() or query.strip()
    except Exception as exc:
        logging.error(f"Query rewrite failed: {exc}")
        return query.strip()


def compact_memory(previous_memory, user_query, assistant_answer):
    previous_memory = previous_memory or {}
    existing_summary = (previous_memory.get("summary") or "").strip()
    messages = sanitize_messages(previous_memory.get("messages") or [])
    messages.extend([
        {"role": "user", "content": user_query.strip()[:MAX_MESSAGE_CHARS]},
        {"role": "assistant", "content": assistant_answer.strip()[:MAX_MESSAGE_CHARS]},
    ])

    if len(messages) <= SUMMARY_TRIGGER_LIMIT:
        return {
            "summary": existing_summary,
            "messages": messages,
            "recentCount": len(messages),
            "summarizedCount": 0
        }

    messages_to_summarize = messages[:-RECENT_MESSAGE_LIMIT]
    recent_messages = messages[-RECENT_MESSAGE_LIMIT:]
    system_prompt = (
        "Maintain a compact conversation memory summary for a RAG assistant. "
        "Preserve user goals, referenced topics, constraints, resolved entities, and important answers. "
        "Do not invent facts. Keep it concise."
    )
    user_prompt = f"""
Existing memory summary:
{existing_summary or 'None'}

Older conversation turns to fold into memory:
{format_messages(messages_to_summarize)}

Updated compact summary:
"""

    try:
        updated_summary = complete_text(system_prompt, user_prompt)
    except Exception as exc:
        logging.error(f"Conversation summarization failed: {exc}")
        older_text = format_messages(messages_to_summarize)
        updated_summary = "\n".join(part for part in [existing_summary, older_text] if part)[-3000:]

    return {
        "summary": updated_summary.strip(),
        "messages": recent_messages,
        "recentCount": len(recent_messages),
        "summarizedCount": len(messages_to_summarize)
    }
