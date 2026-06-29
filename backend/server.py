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
