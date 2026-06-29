import logging
import os
import cohere
from dotenv import load_dotenv

load_dotenv()

logging.info("Step 1: Loading Cohere model")

# Cohere embed-english-v3.0 is 1024-dim, similar to previous BGE
co = cohere.Client(os.environ.get("COHERE_API_KEY"))

logging.info("Step 2: Cohere client loaded")

def get_embeddings(chunks, input_type="search_document"):

    logging.info(f"Creating embeddings for {len(chunks)} chunks using Cohere")

    response = co.embed(
        texts=chunks,
        model='embed-english-v3.0',
        input_type=input_type
    )
    return response.embeddings

