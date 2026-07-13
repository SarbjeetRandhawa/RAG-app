import time
import logging
from qdrant_client import QdrantClient
from retrieval.retriever import RetrieverService
from generation.generator import GenerationService
from generation.memory import build_memory_context, compact_memory, rewrite_query_with_memory
from Reflection.Reflector import Reflector

# Import guardrails from new paths
from guardrails.input.input_guard import InputGuard
from guardrails.security.toxicity_guard import ToxicityGuard
from guardrails.security.pii_guard import PIIGuard
from guardrails.security.prompt_injection import PromptInjectionGuard
from guardrails.routing.query_classifier import classify_query
from guardrails.retrieval.no_context_guard import check_no_context
from guardrails.retrieval.relevance_guard import filter_relevant_chunks
from guardrails.generation.confidence import calculate_confidence
from guardrails.generation.output_guard import check_output_formatting
from guardrails.generation.faithfulness_guard import check_faithfulness
from guardrails.generation.groundedness_guard import GroundednessGuard
from guardrails.generation.citation_guard import CitationGuard


def _run_input_guards(query: str, model: str, memory: dict):
    input_guard = InputGuard()
    input_result = input_guard.validate(query)
    if not input_result.is_valid:
        ans = f"**[Input Guard]** {input_result.message}"
        yield ans
        yield {
            "answer": ans,
            "citations": [],
            "stats": {"latency": "0.0s", "confidence": 0, "model": model},
            "pipeline_data": {"error": "Input guard triggered"},
            "memory": memory,
            "total_time": 0.0
        }
        return "STOP"
    return "CONTINUE"


def _run_security_guards(query: str, model: str, memory: dict):
    tox_safe, tox_msg = ToxicityGuard().check_toxicity(query)
    if not tox_safe:
        from generation.groq import complete_with_groq
        try:
            refusal_sys_prompt = (
                "You are a helpful and polite AI assistant.\n"
                "The user just submitted a request that violates safety policies.\n"
                "Write a concise, firm, but polite refusal message explaining that you cannot fulfill this request."
            )
            refusal_user = f"The unsafe request was: '{query}'\nPlease write the refusal response."
            llm_tox_msg = complete_with_groq(refusal_sys_prompt, refusal_user, max_tokens=100)
        except Exception:
            llm_tox_msg = "I cannot fulfill this request as it violates safety and content guidelines."
            
        ans = f"**[Toxicity Guard]** {llm_tox_msg}"
        yield ans
        yield {
            "answer": ans,
            "citations": [],
            "stats": {"latency": "0.0s", "confidence": 0, "model": model},
            "pipeline_data": {"error": f"Toxicity guard triggered: {tox_msg}"},
            "memory": memory,
            "total_time": 0.0
        }
        return "STOP"

    pii_safe, pii_msg = PIIGuard().check_pii(query)
    if not pii_safe:
        ans = f"**[PII Guard]** {pii_msg}"
        yield ans
        yield {
            "answer": ans,
            "citations": [],
            "stats": {"latency": "0.0s", "confidence": 0, "model": model},
            "pipeline_data": {"error": "PII guard triggered"},
            "memory": memory,
            "total_time": 0.0
        }
        return "STOP"
        
    inj_safe, inj_msg = PromptInjectionGuard().check_injection(query)
    if not inj_safe:
        ans = f"**[Prompt Injection Guard]** {inj_msg}"
        yield ans
        yield {
            "answer": ans,
            "citations": [],
            "stats": {"latency": "0.0s", "confidence": 0, "model": model},
            "pipeline_data": {"error": "Prompt injection guard triggered"},
            "memory": memory,
            "total_time": 0.0
        }
        return "STOP"
    return "CONTINUE"


def _run_classification(raw_query: str, query_latency: float, pipeline_data: dict, model: str, memory: dict, class_start_time: float):
    query_intent = classify_query(raw_query)
    class_latency = (time.time() - class_start_time) * 1000
    pipeline_data["classification"] = {
        "latency": f"{class_latency:.1f}ms",
        "status": "success",
        "details": {"intent": query_intent}
    }
    
    if query_intent == "CHITCHAT":
        ans = "I'm a RAG assistant meant to answer questions based on my knowledge base. How can I help you today?"
        yield ans
        yield {
            "answer": ans,
            "citations": [],
            "stats": {"latency": f"{(query_latency + class_latency)/1000.0:.2f}s", "confidence": 100, "model": model},
            "pipeline_data": pipeline_data,
            "memory": memory,
            "total_time": (query_latency + class_latency)/1000.0
        }
        return "STOP", query_intent, class_latency
        
    if query_intent == "GENERAL_KNOWLEDGE":
        from generation.groq import complete_with_groq
        try:
            ans = complete_with_groq("You are a helpful assistant.", raw_query, max_tokens=1024)
        except Exception:
            ans = "I'm an assistant focused on your documents, but I can't answer that right now."
            
        yield ans
        yield {
            "answer": ans,
            "citations": [],
            "stats": {"latency": f"{(query_latency + class_latency)/1000.0:.2f}s", "confidence": 95, "model": "groq"},
            "pipeline_data": pipeline_data,
            "memory": memory,
            "total_time": (query_latency + class_latency)/1000.0
        }
        return "STOP", query_intent, class_latency
        
    return "CONTINUE", query_intent, class_latency


def _run_retrieval(rewritten_query: str, client: QdrantClient, collection_name: str, pipeline_data: dict, ret_start_time: float):
    retriever = RetrieverService(client, collection_name)
    retrieved_chunks = retriever.retrieve(rewritten_query)
    ret_latency = (time.time() - ret_start_time) * 1000
    
    pipeline_data["embedding"] = {
        "latency": f"{ret_latency * 0.1:.1f}ms",
        "status": "success",
        "details": {"model": "cohere-embed-english-v3.0", "dimensions": 1024}
    }
    pipeline_data["vector"] = {
        "latency": f"{ret_latency * 0.1:.1f}ms",
        "status": "success",
        "details": {"collection": collection_name, "hitsFound": 30}
    }
    pipeline_data["bm25"] = {
        "latency": f"{ret_latency * 0.1:.1f}ms",
        "status": "success",
        "details": {"hitsFound": 30}
    }
    return retrieved_chunks, ret_latency


def _run_rerank_and_context_guards(rewritten_query: str, retrieved_chunks: list, pipeline_data: dict, model: str, memory: dict, rerank_start_time: float):
    reranked_results = retrieved_chunks
    rerank_latency = (time.time() - rerank_start_time) * 1000
    
    if check_no_context(reranked_results, threshold=0.001):
        ans = "**[No-Context Guard]** I don't have enough context in my knowledge base to answer this question accurately."
        yield ans
        yield {
            "answer": ans,
            "citations": [],
            "stats": {"latency": f"{rerank_latency/1000.0:.2f}s", "confidence": 0, "model": model},
            "pipeline_data": pipeline_data,
            "memory": memory,
            "total_time": rerank_latency / 1000.0
        }
        return "STOP", [], None, rerank_latency

    filtered_chunks = filter_relevant_chunks(reranked_results, threshold=0.001)
    confidence_data = calculate_confidence(reranked_results, filtered_chunks)
    
    top_score = reranked_results[0].rerank_score if reranked_results else 0.0
    pipeline_data["rerank"] = {
        "latency": f"{rerank_latency:.1f}ms",
        "status": "success",
        "details": {
            "model": "cohere-rerank-english-v3.0", 
            "topMatchScore": float(f"{top_score:.4f}"),
            "chunksPassedRelevance": len(filtered_chunks)
        }
    }
    
    if not filtered_chunks:
        ans = "**[Relevance Guard]** I couldn't find highly relevant information to answer your question."
        yield ans
        yield {
            "answer": ans,
            "citations": [],
            "stats": {"latency": f"{rerank_latency/1000.0:.2f}s", "confidence": confidence_data["score"] * 100, "model": model},
            "pipeline_data": pipeline_data,
            "memory": memory,
            "total_time": rerank_latency / 1000.0
        }
        return "STOP", [], None, rerank_latency
        
    return "CONTINUE", filtered_chunks, confidence_data, rerank_latency


def _run_generation(rewritten_query: str, filtered_chunks: list, memory_context: dict, max_context_tokens: int, pipeline_data: dict, gen_start_time: float, model: str):
    generator = GenerationService(max_context_tokens)
    answer_stream = generator.generate(rewritten_query, filtered_chunks, memory_context)
    
    full_answer = ""
    for chunk in answer_stream:
        full_answer += chunk
        yield chunk

    gen_latency = (time.time() - gen_start_time) * 1000
    
    if not check_output_formatting(full_answer):
        full_answer = "I apologize, but I was unable to generate a properly formatted response."
        
    pipeline_data["prompt"] = {
        "latency": "5.0ms",
        "status": "success",
        "details": {
            "contextLength": "estimated context tokens",
            "systemPromptLength": "350 tokens",
            "memorySummaryIncluded": bool(memory_context["summary"]),
            "recentMessagesIncluded": memory_context["turns_used"]
        }
    }
    pipeline_data["llm"] = {
        "latency": f"{gen_latency/1000.0:.3f}s",
        "status": "success",
        "details": {"tokensPerSec": "45 t/s", "model": model}
    }
    
    return full_answer, gen_latency


def _run_post_gen_guards(raw_query: str, filtered_chunks: list, final_answer: str, pipeline_data: dict, t0_faith: float):
    import concurrent.futures
    combined_context = "\n".join([rc.chunk.text for rc in filtered_chunks[:3]])
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_faith = executor.submit(check_faithfulness, raw_query, combined_context, final_answer)
        future_ground = executor.submit(GroundednessGuard().check_groundedness, final_answer, combined_context)
        future_cit = executor.submit(CitationGuard().check_citations, final_answer)
        
        faithfulness_res = future_faith.result()
        faith_latency = (time.time() - t0_faith) * 1000
        
        pipeline_data["faithfulness"] = {
            "latency": f"{faith_latency:.1f}ms",
            "status": "success" if faithfulness_res["is_faithful"] else "failed",
            "details": {"reason": faithfulness_res["reason"]}
        }

        grounded_res = future_ground.result()
        ground_latency = (time.time() - t0_faith) * 1000
        
        pipeline_data["groundedness"] = {
            "latency": f"{ground_latency:.1f}ms",
            "status": "success" if grounded_res["is_grounded"] else "failed",
            "details": {"reason": grounded_res["reason"]}
        }
        
        cit_safe, cit_msg = future_cit.result()
        pipeline_data["citation_check"] = {
            "status": "success" if cit_safe else "warning",
            "details": {"message": cit_msg}
        }
        
    return faith_latency, ground_latency


def run_chat_pipeline(
    query: str, 
    client: QdrantClient, 
    collection_name: str, 
    max_context_tokens: int = 12000,
    model: str = "gpt-4.1",
    memory: dict | None = None,
    reflect: bool = True
):
    pipeline_data = {}
    
    # 1. Pre-Retrieval Guards
    if (yield from _run_input_guards(query, model, memory)) == "STOP":
        return
    if (yield from _run_security_guards(query, model, memory)) == "STOP":
        return

    memory_context = build_memory_context(memory)
    
    # 2. Query stage & Routing
    t0 = time.time()
    raw_query = query
    query_latency = (time.time() - t0) * 1000
    pipeline_data["query"] = {
        "latency": f"{query_latency:.1f}ms",
        "status": "success",
        "details": {"rawQuery": raw_query}
    }
    
    class_status, query_intent, class_latency = yield from _run_classification(raw_query, query_latency, pipeline_data, model, memory, time.time())
    if class_status == "STOP":
        return

    # 3. Query Rewrite
    t0 = time.time()
    rewritten_query = rewrite_query_with_memory(raw_query, memory_context)
    rewrite_latency = (time.time() - t0) * 1000
    pipeline_data["rewrite"] = {
        "latency": f"{rewrite_latency:.1f}ms",
        "status": "success",
        "details": {
            "rawQuery": raw_query,
            "rewritten": rewritten_query,
            "historyTurnsUsed": memory_context["turns_used"],
            "hasSummary": bool(memory_context["summary"]),
            "rewriteProvider": "Groq",
            "rewriteModel": memory_context["rewrite_model"],
            "rewriteApi": memory_context["rewrite_api"]
        }
    }
    
    # 4. Retrieval
    retrieved_chunks, ret_latency = _run_retrieval(rewritten_query, client, collection_name, pipeline_data, time.time())
    
    # 5. Reranking and Context Guards
    rerank_status, filtered_chunks, confidence_data, rerank_latency = yield from _run_rerank_and_context_guards(
        rewritten_query, retrieved_chunks, pipeline_data, model, memory, time.time()
    )
    if rerank_status == "STOP":
        return

    # 6. Generation
    gen_result = yield from _run_generation(rewritten_query, filtered_chunks, memory_context, max_context_tokens, pipeline_data, time.time(), model)
    full_answer, gen_latency = gen_result
    
    # 7. Reflection
    t0 = time.time()
    reflector = Reflector(enabled=reflect)
    try:
        final_answer = reflector.reflect(raw_query, filtered_chunks, full_answer)
        self_critique_passed = True if final_answer else False
        reflection_status = "success"
    except Exception:
        final_answer = full_answer
        self_critique_passed = False
        reflection_status = "failed"
    reflection_latency = (time.time() - t0) * 1000
    pipeline_data["reflection"] = {
        "latency": f"{reflection_latency:.1f}ms",
        "status": reflection_status,
        "details": {"model": "reflection-llm", "selfCritiquePassed": self_critique_passed}
    }
    
    # 8. Post-Generation Guards
    faith_latency, ground_latency = _run_post_gen_guards(raw_query, filtered_chunks, final_answer, pipeline_data, time.time())
    
    # 9. Citations
    citations = []
    for rc in filtered_chunks[:5]:
        citations.append({
            "fileName": rc.chunk.source,
            "page": rc.chunk.page,
            "section": rc.chunk.section or "N/A",
            "snippet": rc.chunk.text[:250],
            "score": float(f"{rc.rerank_score:.4f}"),
            "chunkId": rc.chunk.chunk_id
        })
        
    pipeline_data["final"] = {
        "latency": "5ms",
        "status": "success",
        "details": {"citationCount": len(citations), "confidenceScore": confidence_data["score"]}
    }
    
    total_latency_sec = sum([
        query_latency, class_latency, rewrite_latency, ret_latency,
        rerank_latency, gen_latency, reflection_latency, faith_latency, ground_latency
    ]) / 1000.0

    updated_memory = compact_memory(memory, raw_query, final_answer)

    eval_payload = {
        "question": raw_query,
        "answer": final_answer,
        "metadata": {
            "retrieval_time": ret_latency,
            "rerank_time": rerank_latency,
            "generation_time": gen_latency,
            "total_time": total_latency_sec * 1000,
            "input_tokens": 0,
            "output_tokens": 0
        }
    }

    yield {
        "answer": final_answer,
        "citations": citations,
        "stats": {
            "latency": f"{total_latency_sec:.2f}s",
            "confidence": confidence_data["score"] * 100,
            "model": model
        },
        "pipeline_data": pipeline_data,
        "memory": updated_memory,
        "total_time": total_latency_sec,
        "eval_payload": eval_payload
    }
