import os
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    MetaData,
    String,
    Table,
    Text,
    create_engine,
    delete,
    func,
    select,
    insert,
    update,
)

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+psycopg2://postgres:postgres@localhost:5433/Rag_learning"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
metadata = MetaData()

chat_sessions = Table(
    "chat_sessions",
    metadata,
    Column("id", String, primary_key=True),
    Column("title", String(255), nullable=False),
    Column("collection_id", String(100), nullable=True),
    Column("memory_summary", Text, nullable=False, default=""),
    Column("recent_messages", JSON, nullable=False, default=list),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
)

chat_messages = Table(
    "chat_messages",
    metadata,
    Column("id", String, primary_key=True),
    Column("session_id", String, nullable=False),
    Column("role", String(20), nullable=False),
    Column("content", Text, nullable=False),
    Column("citations", JSON, nullable=True),
    Column("stats", JSON, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
)


def now_utc():
    return datetime.now(timezone.utc)


def init_db():
    metadata.create_all(engine)


def serialize_datetime(value):
    return value.isoformat() if value else None


def create_chat_session(title="New Chat Session", collection_id="col1"):
    session_id = f"chat_{uuid.uuid4().hex}"
    timestamp = now_utc()
    with engine.begin() as conn:
        conn.execute(
            insert(chat_sessions).values(
                id=session_id,
                title=title,
                collection_id=collection_id,
                memory_summary="",
                recent_messages=[],
                created_at=timestamp,
                updated_at=timestamp,
            )
        )
    return get_chat_session(session_id)


def get_chat_session(session_id):
    with engine.begin() as conn:
        row = conn.execute(
            select(chat_sessions).where(chat_sessions.c.id == session_id)
        ).mappings().first()
    if not row:
        return None
    return {
        "id": row["id"],
        "title": row["title"],
        "collectionId": row["collection_id"],
        "memory": {
            "summary": row["memory_summary"] or "",
            "recentMessages": row["recent_messages"] or [],
        },
        "createdAt": serialize_datetime(row["created_at"]),
        "updatedAt": serialize_datetime(row["updated_at"]),
    }


def list_chat_sessions():
    with engine.begin() as conn:
        rows = conn.execute(
            select(chat_sessions).order_by(chat_sessions.c.updated_at.desc())
        ).mappings().all()
    return [
        {
            "id": row["id"],
            "title": row["title"],
            "collectionId": row["collection_id"],
            "createdAt": serialize_datetime(row["created_at"]),
            "updatedAt": serialize_datetime(row["updated_at"]),
        }
        for row in rows
    ]


def delete_empty_chat_sessions():
    message_counts = (
        select(
            chat_messages.c.session_id,
            func.count(chat_messages.c.id).label("message_count")
        )
        .group_by(chat_messages.c.session_id)
        .subquery()
    )

    empty_session_ids = (
        select(chat_sessions.c.id)
        .outerjoin(message_counts, chat_sessions.c.id == message_counts.c.session_id)
        .where(message_counts.c.message_count.is_(None))
    )

    with engine.begin() as conn:
        result = conn.execute(
            delete(chat_sessions).where(chat_sessions.c.id.in_(empty_session_ids))
        )
    return result.rowcount or 0


def get_session_messages(session_id):
    with engine.begin() as conn:
        rows = conn.execute(
            select(chat_messages)
            .where(chat_messages.c.session_id == session_id)
            .order_by(chat_messages.c.created_at.asc())
        ).mappings().all()
    return [
        {
            "id": row["id"],
            "role": row["role"],
            "content": row["content"],
            "citations": row["citations"] or [],
            "stats": row["stats"] or {},
            "createdAt": serialize_datetime(row["created_at"]),
        }
        for row in rows
    ]


def get_session_memory(session_id):
    session = get_chat_session(session_id)
    if not session:
        return {"summary": "", "messages": []}
    return {
        "summary": session["memory"]["summary"],
        "messages": session["memory"]["recentMessages"],
    }


def add_chat_message(session_id, role, content, citations=None, stats=None):
    message_id = f"msg_{uuid.uuid4().hex}"
    timestamp = now_utc()
    with engine.begin() as conn:
        conn.execute(
            insert(chat_messages).values(
                id=message_id,
                session_id=session_id,
                role=role,
                content=content,
                citations=citations or [],
                stats=stats or {},
                created_at=timestamp,
            )
        )
        conn.execute(
            update(chat_sessions)
            .where(chat_sessions.c.id == session_id)
            .values(updated_at=timestamp)
        )
    return message_id


def update_session_title_if_default(session_id, query):
    session = get_chat_session(session_id)
    if not session or not session["title"].startswith("New Chat Session"):
        return
    title = query.strip()
    if len(title) > 28:
        title = title[:28] + "..."
    if not title:
        return
    with engine.begin() as conn:
        conn.execute(
            update(chat_sessions)
            .where(chat_sessions.c.id == session_id)
            .values(title=title, updated_at=now_utc())
        )


def update_session_memory(session_id, memory):
    memory = memory or {}
    with engine.begin() as conn:
        conn.execute(
            update(chat_sessions)
            .where(chat_sessions.c.id == session_id)
            .values(
                memory_summary=memory.get("summary") or "",
                recent_messages=memory.get("recentMessages") or [],
                updated_at=now_utc(),
            )
        )
