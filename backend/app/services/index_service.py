"""
Index service — RAG ingestion pipeline (four stages):

  1. Loading   — read the PDF from the upload, extract plain text
  2. Chunking  — split text into overlapping segments for retrieval
  3. Embedding — turn each chunk into a vector (OpenAI embeddings)
  4. Store     — save vectors + text + metadata in the vector DB (Chroma)
"""

import io
import uuid

import chromadb
from fastapi import HTTPException, UploadFile
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
from PyPDF2 import PdfReader

from app.core.config import settings


def _bad_request(msg: str) -> None:
    raise HTTPException(status_code=400, detail=msg)


async def index_document(file: UploadFile) -> dict:
    """
    Run loading → chunking → embedding → store for one PDF.
    Returns {"status": "success", "chunks": <int>}.
    """

    # ── Stage 1: Loading — read upload bytes, parse PDF, extract text ────────

    raw_bytes = await file.read()
    reader = PdfReader(io.BytesIO(raw_bytes))
    pages_text = [page.extract_text() or "" for page in reader.pages]
    full_text = "\n".join(pages_text)

    # ── Stage 2: Chunking — split full text into retrieval-sized pieces ─────

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.index_chunk_size,
        chunk_overlap=settings.index_chunk_overlap,
        separators=["\n\n", "\n", " ", ""],
    )
    chunks: list[str] = splitter.split_text(full_text)

    documents = [
        Document(page_content=chunk, metadata={"source": file.filename, "chunk_index": i})
        for i, chunk in enumerate(chunks)
    ]

    if not settings.openai_api_key:
        _bad_request("Add OPENAI_API_KEY in backend/.env.local")

    # ── Stage 3: Embedding — vectorise each chunk for semantic search ─────────

    try:
        embeddings = OpenAIEmbeddings(
            model=settings.index_embedding_model,
            openai_api_key=settings.openai_api_key,  # type: ignore[arg-type]
        )
        vectors: list[list[float]] = embeddings.embed_documents(
            [d.page_content for d in documents]
        )

        # ── Stage 4: Store in vector database (Chroma: vectors, text, metadata) ─

        client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
        collection = client.get_or_create_collection(name=settings.collection_name)
        collection.add(
            ids=[str(uuid.uuid4()) for _ in documents],
            embeddings=vectors,
            documents=[d.page_content for d in documents],
            metadatas=[d.metadata for d in documents],
        )
    except Exception:
        _bad_request("Indexing failed — check your API key and try again.")

    return {"status": "success", "chunks": len(documents)}
