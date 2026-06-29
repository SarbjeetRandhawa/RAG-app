import os
from langchain_text_splitters import RecursiveCharacterTextSplitter
from models.chunk import Chunk

_tokenizer = None

def get_tokenizer():
    global _tokenizer
    if _tokenizer is None:
        try:
            from transformers import AutoTokenizer
            _tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")
        except Exception:
            pass
    return _tokenizer

def chunk_text(pages_data):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100
    )

    tokenizer = get_tokenizer()
    chunks_data = []
    chunk_index = 0

    for page in pages_data:
        chunks = splitter.split_text(page["text"])
        source = page["source"]
        document_id = os.path.splitext(os.path.basename(source))[0]

        for chunk in chunks:
            chunk_id = f"{document_id}_chunk_{chunk_index}"
            
            if tokenizer:
                token_count = len(tokenizer.encode(chunk, add_special_tokens=False))
            else:
                token_count = len(chunk.split())  # simple word count fallback

            chunks_data.append(Chunk(
                chunk_id=chunk_id,
                document_id=document_id,
                page=page["page"],
                section=page["section"],
                source=source,
                chunk_index=chunk_index,
                token_count=token_count,
                text=chunk
            ))
            chunk_index += 1

    return chunks_data