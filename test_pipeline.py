import sys
import os

# Add project root to python path
sys.path.append("d:/Rag Learning")

from ingestion.extract import extract_text
from ingestion.clean import clean_text
from ingestion.chunk import chunk_text
from ingestion.embed import get_embeddings
from models.reranker import rerank
from models.chunk import Chunk

def main():
    print("Testing extraction, cleaning, and chunking...")
    pdf_path = "data/data.pdf"
    
    pages = extract_text(pdf_path)
    print(f"Extracted {len(pages)} pages.")
    
    cleaned_pages = clean_text(pages)
    print("Cleaned pages.")
    
    chunks = chunk_text(cleaned_pages)
    print(f"Generated {len(chunks)} chunks.")
    
    if not chunks:
        print("Error: No chunks generated!")
        sys.exit(1)
        
    first_chunk = chunks[0]
    print(f"First chunk structure: {first_chunk}")
    assert isinstance(first_chunk, Chunk), "First chunk must be a Chunk object"
    assert first_chunk.token_count > 0, "Token count should be greater than 0"
    assert first_chunk.document_id == "data", f"document_id should be 'data', got {first_chunk.document_id}"
    
    print("Testing embed...")
    embeddings = get_embeddings([first_chunk.text])
    print(f"Generated embedding of size: {len(embeddings[0])}")
    
    print("Testing reranker...")
    reranked = rerank("What is this document about?", chunks[:5])
    print("Reranked successfully.")
    for c in reranked:
        print(f"Chunk ID: {c.chunk_id} | Score: {c.score:.4f} | Tokens: {c.token_count}")
        
    print("\nAll pipeline components verified successfully!")

if __name__ == "__main__":
    main()

