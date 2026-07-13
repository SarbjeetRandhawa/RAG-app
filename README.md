# 🚀 Enterprise RAG Studio (AetherRAG)

An advanced, production-ready Retrieval-Augmented Generation (RAG) application with an elegant UI and a powerful backend. This system provides highly accurate, hallucination-free answers from your enterprise documents by utilizing multi-stage retrieval, semantic caching, reranking, and self-reflection.

## ✨ Key Features

- **Multi-Stage Retrieval Pipeline**: Combines dense vector search (Qdrant) and sparse keyword search (BM25) for robust hybrid retrieval.
- **Cross-Encoder Reranking**: Uses Cohere's rerank models to ensure the most semantically relevant document chunks are prioritized.
- **Self-Reflection & Guardrails**: Automatically self-critiques generated answers, utilizing asynchronous Faithfulness, Groundedness, and Citation guardrails.
- **Semantic Caching**: Integrates Redis for semantic caching of responses, drastically reducing latency and LLM costs for semantically similar queries.
- **Query Rewriting**: Dynamically expands and rewrites queries based on conversational chat history to resolve pronouns and context.
- **Real-Time Pipeline Inspector**: The frontend features a beautiful, real-time visualizer for each step of the RAG pipeline.
- **Rich Document Management**: Upload PDFs (using PyMuPDF/Docling), manage collections, and inspect ingestion analytics.

## 🛠️ Tech Stack

### Frontend
- **Framework**: React 19 + Vite
- **Styling**: TailwindCSS v4 with custom design tokens for a premium aesthetic
- **Components**: Lucide React for iconography, React Markdown with GitHub Flavored Markdown (GFM) for rich chat rendering

### Backend
- **Framework**: FastAPI (Python)
- **Vector Database**: Qdrant
- **Keyword Search**: BM25
- **LLM Integrations**: Azure OpenAI (GPT-4.1), Groq, Cohere, Llama.cpp (Local)
- **Evaluation**: DeepEval for objective RAG metrics
- **Caching**: Redis (Semantic Cache & Session Cache)

---

## 🚀 Getting Started

Follow these instructions to set up the project locally.

### Prerequisites
- Python 3.10+
- Node.js 18+
- Redis (running locally on port 6379 or via Docker)
- Required API Keys: OpenAI (or Azure), Cohere, Groq

### 1. Backend Setup

1. **Navigate to the backend directory:**
   ```bash
   cd backend
   ```

2. **Create a virtual environment and activate it:**
   ```bash
   python -m venv .venv
   
   # On Windows:
   .venv\Scripts\activate
   # On macOS/Linux:
   source .venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables:**
   Create a `.env` file in the `backend` directory and configure your keys:
   ```env
   OPENAI_API_KEY=your_openai_api_key
   COHERE_API_KEY=your_cohere_api_key
   GROQ_API_KEY=your_groq_api_key
   ```
   *(Note: The system connects to Redis on `localhost:6379` by default).*

5. **Start the FastAPI Server:**
   ```bash
   python server.py
   ```
   *The backend API will run on http://localhost:8000. You can view the swagger docs at http://localhost:8000/docs.*

### 2. Frontend Setup

1. **Navigate to the frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Start the development server:**
   ```bash
   npm run dev
   ```
   *The frontend application will be available at http://localhost:5173.*

---

## 🏗️ Architecture Overview

The system operates across two primary pipelines: the **Document Ingestion Pipeline** and the **Retrieval & Generation (Chat) Pipeline**.

### 1. Document Ingestion Pipeline
Before the system can answer queries, knowledge must be ingested. The ingestion pipeline processes raw documents into searchable vectors and keyword structures:
- **Document Parsers**: Supports parsing files through multiple advanced loaders, including **PyMuPDF** for standard fast PDF extraction and **Docling** for deep semantic parsing.
- **Chunking Strategy**: Documents are parsed, cleaned, and split into manageable semantic chunks using overlapping text splitters to preserve context between neighboring chunks.
- **Dual Indexing**:
  - **Dense Embedding Index (Qdrant)**: Each chunk is passed through an Embedding Model (e.g., Cohere `embed-english-v3.0`) and inserted into a Qdrant vector database for semantic similarity searches.
  - **Sparse Keyword Index (BM25)**: The same chunks are processed by a BM25 indexer to allow for exact keyword matches, which is critical for specific entity retrieval (e.g., product IDs, precise names).
- **Metadata Tagging**: Each chunk is tagged with metadata (page numbers, authors, collection tags) to allow for pre-filtering during retrieval.

### 2. Retrieval & Generation Pipeline (Chat)
When a user submits a query, the system executes a rigorous, multi-stage retrieval architecture to guarantee accuracy and mitigate hallucinations:
- **Semantic Cache Lookup**: Before hitting the LLMs, the system compares the query's embedding against previously answered questions stored in **Redis**. If an exact semantic match is found, it returns the cached response instantly, avoiding pipeline latency.
- **Query Intent Classification**: A classifier analyzes the query to determine if it is `DOMAIN_SPECIFIC`, `GENERAL_KNOWLEDGE`, or `CHITCHAT`. This routing prevents unnecessary database lookups for simple conversational pleasantries.
- **Query Rewrite**: A lightweight LLM (such as Groq) is used to inject context from the user's conversational history. For example, rewriting *"What is their policy?"* into *"What is the company's remote work policy?"*.
- **Hybrid Retrieval**: The rewritten query is sent to both Qdrant (dense vectors) and BM25 (sparse keywords). Both systems return candidate chunks, combining the strengths of semantic understanding and exact keyword precision.
- **Cross-Encoder Reranking**: The merged chunks are passed through a Cohere Reranker model, which re-scores the retrieved context against the user query, promoting only the absolute most relevant chunks to the final context window.
- **LLM Generation**: The top-reranked chunks and the system prompts are fed into a powerful Generator LLM (e.g., Azure OpenAI GPT-4.1) which streams a finalized answer to the frontend UI in real-time.
- **Asynchronous Guardrails & Reflection**: Immediately after generation, background tasks concurrently verify the output:
  - **Reflector**: An LLM agent self-critiques the generated response to ensure high quality.
  - **Faithfulness Guard**: Validates that the answer directly originates from the provided context.
  - **Groundedness Guard**: Ensures no external hallucinations were added to the answer.
  - **Citation Guard**: Validates safe formatting of in-line citations mapped to source chunk pages.
