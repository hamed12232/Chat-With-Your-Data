"""
Index service — four-step RAG ingestion pipeline:
  1. Upload  → read raw PDF bytes from the UploadFile
  2. Chunk   → split extracted text with RecursiveCharacterTextSplitter
  3. Embed   → vectorise chunks with OpenAI text-embedding-3-small
  4. Store   → persist vectors + metadata in a local Chroma collection

Every run writes a structured log file to:
    Logs/indexing/<timestamp>_<filename>.log
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
from app.core.indexing_logger import (
    get_indexing_logger,
    log_pipeline_start,
    log_before_chunks,
    log_after_chunks,
    log_embedding,
    log_vectors_table,
    log_chroma_stored,
    log_pipeline_end,
    log_pipeline_error,
)


async def index_document(file: UploadFile) -> dict:
    """
    Run the full four-step ingestion pipeline for a single uploaded PDF.
    Returns {"status": "success", "chunks": <int>}.
    """

    filename = file.filename or "unknown.pdf"
    logger   = get_indexing_logger(filename)
    start    = log_pipeline_start(logger, filename)

    # ── Step 1 / 4 : Upload ──────────────────────────────────────────────────

    if not file.filename or not file.filename.lower().endswith(".pdf"):
        err = HTTPException(status_code=400, detail="Only PDF files are supported.")
        log_pipeline_error(logger, "1/4 · Upload", err, start)
        raise err

    try:
        raw_bytes = await file.read()
    except Exception as exc:
        err = HTTPException(status_code=500, detail=f"Failed to read file: {exc}")
        log_pipeline_error(logger, "1/4 · Upload", exc, start)
        raise err from exc

    if not raw_bytes:
        err = HTTPException(status_code=400, detail="Uploaded file is empty.")
        log_pipeline_error(logger, "1/4 · Upload", err, start)
        raise err

    file_size = len(raw_bytes)

    # ── Step 2 / 4 : Chunk ───────────────────────────────────────────────────

    try:
        reader     = PdfReader(io.BytesIO(raw_bytes))
        pages_text = [page.extract_text() or "" for page in reader.pages]
        num_pages  = len(pages_text)
        full_text  = "\n".join(pages_text)
    except Exception as exc:
        err = HTTPException(status_code=422, detail=f"PDF parsing failed: {exc}")
        log_pipeline_error(logger, "2/4 · Chunk — PDF parse", exc, start)
        raise err from exc

    if not full_text.strip():
        err = HTTPException(status_code=422, detail="No extractable text found in PDF.")
        log_pipeline_error(logger, "2/4 · Chunk — empty text", err, start)
        raise err

    # Log raw document info BEFORE splitting
    log_before_chunks(logger, filename, file_size, num_pages, full_text)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.index_chunk_size,
        chunk_overlap=settings.index_chunk_overlap,
        separators=["\n\n", "\n", " ", ""],
    )
    chunks: list[str] = splitter.split_text(full_text)

    if not chunks:
        err = HTTPException(status_code=422, detail="Text splitting produced zero chunks.")
        log_pipeline_error(logger, "2/4 · Chunk — zero chunks", err, start)
        raise err

    # Log chunk statistics AFTER splitting
    log_after_chunks(logger, chunks, settings.index_chunk_size, settings.index_chunk_overlap)

    documents = [
        Document(page_content=chunk, metadata={"source": filename, "chunk_index": i})
        for i, chunk in enumerate(chunks)
    ]

    # ── Step 3 / 4 : Embed ───────────────────────────────────────────────────

    if not settings.openai_api_key:
        err = HTTPException(status_code=500, detail="OPENAI_API_KEY is not configured.")
        log_pipeline_error(logger, "3/4 · Embed — missing API key", err, start)
        raise err

    embedding_model = "text-embedding-3-small"

    try:
        embeddings = OpenAIEmbeddings(
            model=embedding_model,
            openai_api_key=settings.openai_api_key,  # type: ignore[arg-type]
        )
    except Exception as exc:
        err = HTTPException(status_code=500, detail=f"Failed to initialise embeddings: {exc}")
        log_pipeline_error(logger, "3/4 · Embed — init", exc, start)
        raise err from exc

    # Embed all chunks in one API call — vectors are captured for logging
    try:
        vectors: list[list[float]] = embeddings.embed_documents(
            [d.page_content for d in documents]
        )
    except Exception as exc:
        err = HTTPException(status_code=500, detail=f"Embedding failed: {exc}")
        log_pipeline_error(logger, "3/4 · Embed — API call", exc, start)
        raise err from exc

    vector_dim = len(vectors[0]) if vectors else 0
    log_embedding(logger, embedding_model, len(chunks), vector_dim)
    log_vectors_table(logger, vectors)

    # ── Step 4 / 4 : Store ───────────────────────────────────────────────────
    # Use raw chromadb so pre-computed vectors are stored as-is (no re-embedding)

    try:
        client     = chromadb.PersistentClient(path=settings.chroma_persist_dir)
        collection = client.get_or_create_collection(name=settings.collection_name)

        # Remove any previously indexed chunks from the same source file so
        # re-uploading the same PDF never creates duplicates in the collection.
        existing = collection.get(where={"source": filename}, include=[])
        if existing["ids"]:
            collection.delete(ids=existing["ids"])

        new_ids = [str(uuid.uuid4()) for _ in documents]
        collection.add(
            ids        = new_ids,
            embeddings = vectors,
            documents  = [d.page_content for d in documents],
            metadatas  = [d.metadata for d in documents],
        )
    except Exception as exc:
        err = HTTPException(status_code=500, detail=f"Chroma storage failed: {exc}")
        log_pipeline_error(logger, "4/4 · Store — Chroma", exc, start)
        raise err from exc

    log_chroma_stored(
        logger,
        collection_name=settings.collection_name,
        persist_dir=settings.chroma_persist_dir,
        num_docs=len(documents),
        collection=collection,
        peek_ids=new_ids,
    )

    log_pipeline_end(logger, filename, len(documents), start)

    return {"status": "success", "chunks": len(documents)}
