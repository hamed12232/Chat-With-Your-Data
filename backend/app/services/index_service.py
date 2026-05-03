"""
Index service — four-step RAG ingestion pipeline:
  1. Upload  → read raw PDF bytes from the UploadFile
  2. Chunk   → split extracted text with RecursiveCharacterTextSplitter
  3. Embed   → vectorise chunks with OpenAI text-embedding-3-small
  4. Store   → persist vectors + metadata in a local Chroma collection
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


async def index_document(file: UploadFile) -> dict:
    """
    Run the full four-step ingestion pipeline for a single uploaded PDF.
    Returns {"status": "success", "chunks": <int>}.
    """

    # ── Step 1 / 4 : Upload ──────────────────────────────────────────────────

    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    try:
        raw_bytes = await file.read()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to read file: {exc}") from exc

    if not raw_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # ── Step 2 / 4 : Chunk ───────────────────────────────────────────────────

    try:
        reader     = PdfReader(io.BytesIO(raw_bytes))
        pages_text = [page.extract_text() or "" for page in reader.pages]
        full_text  = "\n".join(pages_text)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"PDF parsing failed: {exc}") from exc

    if not full_text.strip():
        raise HTTPException(status_code=422, detail="No extractable text found in PDF.")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.index_chunk_size,
        chunk_overlap=settings.index_chunk_overlap,
        separators=["\n\n", "\n", " ", ""],
    )
    chunks: list[str] = splitter.split_text(full_text)

    if not chunks:
        raise HTTPException(status_code=422, detail="Text splitting produced zero chunks.")

    documents = [
        Document(page_content=chunk, metadata={"source": file.filename, "chunk_index": i})
        for i, chunk in enumerate(chunks)
    ]

    # ── Step 3 / 4 : Embed ───────────────────────────────────────────────────

    if not settings.openai_api_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY is not configured.")

    embedding_model = "text-embedding-3-small"

    try:
        embeddings = OpenAIEmbeddings(
            model=embedding_model,
            openai_api_key=settings.openai_api_key,  # type: ignore[arg-type]
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to initialise embeddings: {exc}") from exc

    try:
        vectors: list[list[float]] = embeddings.embed_documents(
            [d.page_content for d in documents]
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Embedding failed: {exc}") from exc

    # ── Step 4 / 4 : Store ───────────────────────────────────────────────────

    try:
        client     = chromadb.PersistentClient(path=settings.chroma_persist_dir)
        collection = client.get_or_create_collection(name=settings.collection_name)
        collection.add(
            ids        = [str(uuid.uuid4()) for _ in documents],
            embeddings = vectors,
            documents  = [d.page_content for d in documents],
            metadatas  = [d.metadata for d in documents],
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Chroma storage failed: {exc}") from exc

    return {"status": "success", "chunks": len(documents)}
