import os
import sys
import uuid
import time
import json
import logging
from typing import List, Optional
from pydantic import BaseModel
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

# Ensure backend directory is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from evaluation.deepeval_runner import run_evaluation, evaluation_results

ENABLE_DEEPEVAL = os.environ.get("ENABLE_DEEPEVAL", "true").lower() == "true"


# Imports from existing proper pipeline modules/code structure
from app import create_collection, ingest_document, COLLECTION_NAME, client
from pipeline.runner import run_chat_pipeline
from db import (
    add_chat_message,
    create_chat_session,
    delete_empty_chat_sessions,
    get_chat_session,
    get_session_memory,
    get_session_messages,
    init_db,
    list_chat_sessions,
    update_session_memory,
    update_session_title_if_default,
)

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

app = FastAPI(title="RAG Backend API")

# Enable CORS for frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MANIFEST_PATH = os.path.join("data", "manifest.json")

# Helper to load/save document manifest
def load_manifest() -> list:
    if not os.path.exists(MANIFEST_PATH):
        # Initialize with default sample document if the file exists
        default_doc = {
            "id": "data",
            "name": "data.pdf",
            "size": "35.5 KB",
            "chunks": 24,
            "status": "Indexed",
            "tags": ["Standard", "PDF"],
            "author": "System",
            "collectionId": "col1",
            "uploadedAt": "2026-06-29"
        }
        return [default_doc]
    try:
        with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_manifest(manifest: list):
    os.makedirs(os.path.dirname(MANIFEST_PATH), exist_ok=True)
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

ANALYTICS_PATH = os.path.join("data", "analytics.json")

def load_analytics() -> dict:
    if not os.path.exists(ANALYTICS_PATH):
        return {"queries": [], "daily_stats": {}}
    try:
        with open(ANALYTICS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"queries": [], "daily_stats": {}}

def save_analytics(data: dict):
    os.makedirs(os.path.dirname(ANALYTICS_PATH), exist_ok=True)
    with open(ANALYTICS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# Pydantic models
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatMemory(BaseModel):
    summary: Optional[str] = ""
    messages: Optional[List[ChatMessage]] = []

class ChatRequest(BaseModel):
    query: str
    model: Optional[str] = "gpt-4.1"
    collectionId: Optional[str] = "col1"
    sessionId: Optional[str] = None
    memory: Optional[ChatMemory] = None

class CreateSessionRequest(BaseModel):
    title: Optional[str] = "New Chat Session"
    collectionId: Optional[str] = "col1"

@app.on_event("startup")
def startup_event():
    init_db()
    create_collection()

@app.get("/api/health")
def health_check():
    try:
        client.get_collections()
        return {"status": "ok", "qdrant": "connected"}
    except Exception as e:
        return {"status": "ok", "qdrant": "disconnected", "error": str(e)}

@app.get("/api/documents")
def get_documents():
    return load_manifest()

@app.get("/api/sessions")
def get_sessions():
    delete_empty_chat_sessions()
    return list_chat_sessions()

@app.post("/api/sessions")
def create_session(req: CreateSessionRequest):
    return create_chat_session(
        title=req.title or "New Chat Session",
        collection_id=req.collectionId or "col1"
    )

@app.get("/api/sessions/{session_id}")
def get_session(session_id: str):
    session = get_chat_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {
        "session": session,
        "messages": get_session_messages(session_id),
        "memory": session["memory"]
    }

@app.post("/api/upload")
async def upload_document(
    file: UploadFile = File(...),
    tags: str = Form("Research, General"),
    author: str = Form("User"),
    collectionId: str = Form("col1")
):
    try:
        file_dir = "data"
        os.makedirs(file_dir, exist_ok=True)
        file_path = os.path.join(file_dir, file.filename)
        
        # Save file to disk
        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)
            
        file_size_kb = len(contents) / 1024
        doc_id = str(uuid.uuid4())
        
        # Reuse existing proper pipeline ingestion function from app.py
        chunks = ingest_document(pdf_path=file_path, document_id=doc_id, filename=file.filename)
        
        # Update manifest
        manifest = load_manifest()
        new_doc = {
            "id": doc_id,
            "name": file.filename,
            "size": f"{file_size_kb:.1f} KB",
            "chunks": len(chunks) if chunks else 0,
            "status": "Indexed",
            "tags": [t.strip() for t in tags.split(",") if t.strip()],
            "author": author,
            "collectionId": collectionId,
            "uploadedAt": time.strftime("%Y-%m-%d")
        }
        manifest.append(new_doc)
        save_manifest(manifest)
        
        return new_doc
    except Exception as e:
        logging.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/documents/{document_id}")
def delete_document(document_id: str):
    try:
        # Delete from Qdrant
        client.delete(
            collection_name=COLLECTION_NAME,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="document_id",
                        match=MatchValue(value=document_id)
                    )
                ]
            )
        )
        
        # Update manifest
        manifest = load_manifest()
        doc_to_delete = None
        for doc in manifest:
            if doc["id"] == document_id:
                doc_to_delete = doc
                break
                
        if doc_to_delete:
            manifest.remove(doc_to_delete)
            save_manifest(manifest)
            
            # Optionally remove local file if name matches
            file_path = os.path.join("data", doc_to_delete["name"])
            if os.path.exists(file_path) and doc_to_delete["name"] != "data.pdf":
                os.remove(file_path)
                
        return {"status": "success", "deleted_id": document_id}
    except Exception as e:
        logging.error(f"Deletion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

from collections import Counter
from datetime import datetime, timedelta

@app.get("/api/analytics")
def get_analytics():
    manifest = load_manifest()
    total_docs = len(manifest)
    total_chunks = sum(doc.get("chunks", 0) for doc in manifest)
    
    analytics = load_analytics()
    
    # Process queries to find top queries
    queries = analytics.get("queries", [])
    query_texts = [q["query"] for q in queries]
    counter = Counter(query_texts)
    top_queries_data = []
    
    for q_text, count in counter.most_common(5):
        # find average latency and confidence for this query
        q_instances = [q for q in queries if q["query"] == q_text]
        avg_conf = sum(q.get("confidence", 0) for q in q_instances) / len(q_instances) if q_instances else 0
        avg_lat = sum(q.get("latency_sec", 0.0) for q in q_instances) / len(q_instances) if q_instances else 0.0
        top_queries_data.append({
            "query": q_text,
            "count": count,
            "confidence": round(avg_conf),
            "latency": f"{avg_lat*1000:.0f}ms"
        })

    # Prepare daily stats (last 7 days)
    daily_stats = analytics.get("daily_stats", {})
    latency_data = []
    query_volume = []
    
    today = datetime.now()
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        d_str = d.strftime("%m-%d")
        
        stat = daily_stats.get(d_str, {"count": 0, "total_embed_ms": 0, "total_llm_ms": 0})
        count = stat["count"]
        avg_embed = (stat["total_embed_ms"] / count) if count > 0 else 0
        avg_llm = (stat["total_llm_ms"] / count) if count > 0 else 0
        
        latency_data.append({
            "label": d.strftime("%a"),
            "embed": round(avg_embed),
            "llm": round(avg_llm)
        })
        query_volume.append({
            "date": d_str,
            "queries": count
        })

    avg_retrieval_latency = f"{sum(d['embed'] for d in latency_data) / max(1, sum(1 for d in latency_data if d['embed']>0)):.0f} ms"
    avg_llm_time = f"{sum(d['llm'] for d in latency_data) / max(1, sum(1 for d in latency_data if d['llm']>0)):.0f} ms"

    return {
        "stats": [
            {"id": "docs", "label": "Indexed Documents", "value": total_docs, "change": "+0% this week", "changeType": "up"},
            {"id": "chunks", "label": "Knowledge Chunks", "value": total_chunks, "change": "+0% this week", "changeType": "up"},
            {"id": "vectors", "label": "Embedded Vectors", "value": total_chunks, "change": "+0% this week", "changeType": "up"},
            {"id": "retrieval", "label": "Avg Retrieval Latency", "value": avg_retrieval_latency, "change": "live", "changeType": "down"},
            {"id": "llm", "label": "Avg LLM Time", "value": avg_llm_time, "change": "live", "changeType": "down"}
        ],
        "topQueries": top_queries_data,
        "latencyData": latency_data,
        "queryVolume": query_volume
    }

@app.post("/api/chat")
def chat_query(req: ChatRequest, background_tasks: BackgroundTasks):
    def generate():
        try:
            session_id = req.sessionId
            if session_id and not get_chat_session(session_id):
                raise HTTPException(status_code=404, detail="Session not found")
            if not session_id:
                session = create_chat_session(collection_id=req.collectionId or "col1")
                session_id = session["id"]

            update_session_title_if_default(session_id, req.query)
            add_chat_message(session_id, "user", req.query)

            request_memory = get_session_memory(session_id)
            result_gen = run_chat_pipeline(
                query=req.query,
                client=client,
                collection_name=COLLECTION_NAME,
                max_context_tokens=6000,
                model=req.model or "gpt-4.1",
                memory=request_memory
            )
            
            for item in result_gen:
                if isinstance(item, str):
                    yield json.dumps({"type": "chunk", "text": item}) + "\n"
                elif isinstance(item, dict):
                    # Log to analytics
                    try:
                        analytics = load_analytics()
                        today_str = datetime.now().strftime("%m-%d")
                        if today_str not in analytics["daily_stats"]:
                            analytics["daily_stats"][today_str] = {"count": 0, "total_embed_ms": 0, "total_llm_ms": 0}
                        
                        pipe_data = item.get("pipeline_data", {})
                        embed_lat = float(pipe_data.get("embedding", {}).get("latency", "0").replace("ms", "")) if "embedding" in pipe_data else 0.0
                        
                        llm_lat_str = pipe_data.get("llm", {}).get("latency", "0s").replace("s", "")
                        llm_lat = float(llm_lat_str) * 1000 if "llm" in pipe_data else 0.0
                        
                        total_time_str = item.get("stats", {}).get("latency", "0s").replace("s", "")
                        total_time_sec = float(total_time_str)
                        
                        analytics["daily_stats"][today_str]["count"] += 1
                        analytics["daily_stats"][today_str]["total_embed_ms"] += embed_lat
                        analytics["daily_stats"][today_str]["total_llm_ms"] += llm_lat
                        
                        analytics.setdefault("queries", []).append({
                            "query": req.query,
                            "confidence": item.get("stats", {}).get("confidence", 0),
                            "latency_sec": total_time_sec,
                            "timestamp": time.time()
                        })
                        save_analytics(analytics)
                    except Exception as log_e:
                        logging.error(f"Failed to log analytics: {log_e}")

                    final_data = {
                        "answer": item["answer"],
                        "citations": item["citations"],
                        "stats": item["stats"],
                        "pipeline_data": item["pipeline_data"],
                        "memory": item.get("memory", {})
                    }
                    add_chat_message(
                        session_id,
                        "assistant",
                        item["answer"],
                        citations=item["citations"],
                        stats=item["stats"]
                    )
                    update_session_memory(session_id, item.get("memory", {}))
                    final_data["sessionId"] = session_id
                    
                    message_id = str(uuid.uuid4())
                    final_data["messageId"] = message_id
                    if ENABLE_DEEPEVAL and "eval_payload" in item:
                        background_tasks.add_task(run_evaluation, message_id, item["eval_payload"])
                    
                    yield json.dumps({"type": "final", "data": final_data}) + "\n"
        except Exception as e:
            logging.error(f"Chat execution failed: {e}")
            yield json.dumps({"type": "error", "error": str(e)}) + "\n"
            
    return StreamingResponse(generate(), media_type="application/x-ndjson", background=background_tasks)

@app.get("/api/evaluate/{message_id}")
def get_evaluation(message_id: str):
    if message_id not in evaluation_results:
        return {"status": "not_found"}
    return evaluation_results[message_id]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
