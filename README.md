# RAG API for Flutter

This repository now contains a backend-only **FastAPI** application designed to be consumed by a Flutter mobile client.

The API preserves the existing RAG pipeline exactly as implemented:

- LangChain retrieval logic
- Chroma vector database
- HuggingFace embeddings (`intfloat/multilingual-e5-base`)
- Google Gemini integration
- PDF document ingestion via the server-side indexing pipeline
- `/chat` endpoint behavior unchanged

---

## Stack

- Backend: [FastAPI](https://fastapi.tiangolo.com/)
- Runtime: [Uvicorn](https://www.uvicorn.org/)
- RAG: [LangChain](https://www.langchain.com/), [Chroma](https://www.trychroma.com/), [HuggingFace embeddings](https://huggingface.co/intfloat/multilingual-e5-base), Gemini
- Documents: PDF ingestion using `PyPDF2`

---

## Prerequisites

- Python 3.11+
- Docker (optional for container deployment)
- A Google Gemini API key

---

## Setup

```bash
cd backend
python -m venv .venv
```

Activate the virtual environment:

- Windows (PowerShell): `.venv\Scripts\Activate.ps1`
- macOS / Linux: `source .venv/bin/activate`

Install dependencies:

```bash
pip install -r requirements.txt
```

Copy `backend/.env.local.example` to `backend/.env.local` and set at least:

- `gemnai_key` (or `google_api_key` / `gemini_api_key`)

Optional environment variables:

- `CHROMA_PERSIST_DIR`
- `COLLECTION_NAME`
- `INDEX_CHUNK_SIZE`
- `INDEX_CHUNK_OVERLAP`
- `INDEX_EMBEDDING_MODEL`
- `CHAT_RETRIEVAL_TOP_K`

---

## Running locally

Start the backend API:

```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000```
open this http://localhost:8000/docs

Available endpoints:

- `GET /health`
- `POST /chat/`
- `POST /index/`

---

## API contract

### `GET /health`

Returns a simple health check:

```json
{ "status": "ok" }
```

### `POST /chat/`

Request body:

```json
{ "message": "..." }
```

or:

```json
{ "question": "..." }
```

Response body:

```json
{ "answer": "..." }
```

### `POST /index/`

This endpoint triggers indexing for PDFs available on the server-side documents folder. It is left in place for backend-managed document ingestion.

---

## Deployment

### Docker

Build and run the backend container:

```bash
cd backend
docker build -t rag-api .
docker run --env-file .env.local -p 8000:8000 rag-api
```

### Railway

1. Create a Railway project and connect this repository.
2. Set environment variables in Railway:
   - `gemnai_key` (or `google_api_key` / `gemini_api_key`)
   - Optional: `CHROMA_PERSIST_DIR`, `COLLECTION_NAME`, `INDEX_CHUNK_SIZE`, `INDEX_CHUNK_OVERLAP`, `INDEX_EMBEDDING_MODEL`, `CHAT_RETRIEVAL_TOP_K`
3. Use the following start command:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Railway will expose the service automatically on the assigned port.

---

## Notes for Flutter clients

Your Flutter app can consume this API directly by calling `/chat/` for RAG-based answers and `/health` for readiness checks.

If you need to trigger document re-indexing from the backend, `/index/` remains available as a server-managed ingestion endpoint.

---

## License

This repository is provided as-is. Add a `LICENSE` file if you want to specify terms explicitly.
