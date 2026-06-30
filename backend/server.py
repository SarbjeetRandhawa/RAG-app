import os
import sys
import uuid
import time
import json
import logging
from typing import List, Optional
from pydantic import BaseModel
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

# Ensure backend directory is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Imports from existing proper pipeline modules/code structure
from app import create_collection, ingest_document, COLLECTION_NAME, client
from pipeline.runner import run_chat_pipeline

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
class ChatRequest(BaseModel):
    query: str
    model: Optional[str] = "gpt-4.1"
    collectionId: Optional[str] = "col1"

@app.on_event("startup")
def startup_event():
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
def chat_query(req: ChatRequest):
    try:
        result = run_chat_pipeline(
            query=req.query,
            client=client,
            collection_name=COLLECTION_NAME,
            max_context_tokens=6000,
            model=req.model or "gpt-4.1"
        )
        
        # Log to analytics
        try:
            analytics = load_analytics()
            today_str = datetime.now().strftime("%m-%d")
            if today_str not in analytics["daily_stats"]:
                analytics["daily_stats"][today_str] = {"count": 0, "total_embed_ms": 0, "total_llm_ms": 0}
            
            # parse out latencies
            pipe_data = result.get("pipeline_data", {})
            embed_lat = float(pipe_data.get("embedding", {}).get("latency", "0").replace("ms", "")) if "embedding" in pipe_data else 0.0
            llm_lat = float(pipe_data.get("llm", {}).get("latency", "0").replace("ms", "")) if "llm" in pipe_data else 0.0
            
            total_time_str = result.get("stats", {}).get("latency", "0s").replace("s", "")
            total_time_sec = float(total_time_str)
            
            analytics["daily_stats"][today_str]["count"] += 1
            analytics["daily_stats"][today_str]["total_embed_ms"] += embed_lat
            analytics["daily_stats"][today_str]["total_llm_ms"] += llm_lat
            
            analytics.setdefault("queries", []).append({
                "query": req.query,
                "confidence": result.get("stats", {}).get("confidence", 0),
                "latency_sec": total_time_sec,
                "timestamp": time.time()
            })
            save_analytics(analytics)
        except Exception as log_e:
            logging.error(f"Failed to log analytics: {log_e}")

        return {
            "answer": result["answer"],
            "citations": result["citations"],
            "stats": result["stats"],
            "pipeline_data": result["pipeline_data"]
        }
    except Exception as e:
        logging.error(f"Chat execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
