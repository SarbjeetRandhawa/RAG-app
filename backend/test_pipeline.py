# import sys
# import os
# import logging

# logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# # Add project root to python path
# sys.path.append("d:/Rag Learning")

# from ingestion.extract import extract_text
# from ingestion.clean import clean_text
# from ingestion.chunk import chunk_text
# from ingestion.embed import get_embeddings
# from models.reranker import rerank
# from models.chunk import Chunk, RetrievedChunk
# from generation.generator import GenerationService

# def main():
#     logging.info("Testing extraction, cleaning, and chunking...")
#     pdf_path = "data/data.pdf"
#     MAX_CONTEXT_TOKENS = 6000
    
#     pages = extract_text(pdf_path)
#     logging.info(f"Extracted {len(pages)} pages.")
    
#     cleaned_pages = clean_text(pages)
#     logging.info("Cleaned pages.")
    
#     chunks = chunk_text(cleaned_pages)
#     logging.info(f"Generated {len(chunks)} chunks.")
    
#     if not chunks:
#         logging.error("No chunks generated!")
#         sys.exit(1)
        
#     first_chunk = chunks[0]
#     logging.info(f"First chunk structure: {first_chunk}")
#     assert isinstance(first_chunk, Chunk), "First chunk must be a Chunk object"
#     assert first_chunk.token_count > 0, "Token count should be greater than 0"
#     assert first_chunk.document_id == "data", f"document_id should be 'data', got {first_chunk.document_id}"
    
#     logging.info("Testing embed...")
#     embeddings = get_embeddings([first_chunk.text])
#     logging.info(f"Generated embedding of size: {len(embeddings[0])}")
    
#     logging.info("Testing reranker...")
#     query = "What is this document about?"
#     retrieved = [RetrievedChunk(chunk=c, vector_score=0.9, rerank_score=0.0) for c in chunks[:5]]
#     reranked = rerank(query, retrieved)
#     logging.info("Reranked successfully.")
#     for rc in reranked:
#         logging.info(f"Chunk ID: {rc.chunk.chunk_id} | Vector Score: {rc.vector_score:.4f} | Rerank Score: {rc.rerank_score:.4f} | Tokens: {rc.chunk.token_count}")

#     logging.info("\nTesting generation...")
#     generator = GenerationService(MAX_CONTEXT_TOKENS)
#     answer = generator.generate(query, reranked)
#     logging.info(f"\nGenerated Answer:\n{answer}")

#     logging.info("\nAll pipeline components verified successfully!")

# if __name__ == "__main__":
#     main()

from llama_cpp import Llama

llm = Llama(
    model_path="models/Qwen3-8B-Q4_K_M.gguf",
    n_ctx=4096,
    verbose=False
)

response = llm.create_chat_completion(
    messages=[
        {
            "role": "user",
            "content": "Hello"
        }
    ]
)

print(response["choices"][0]["message"]["content"])