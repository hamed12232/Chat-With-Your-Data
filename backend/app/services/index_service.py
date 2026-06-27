"""
Index service — RAG ingestion pipeline (four stages):

  1. Loading   — read the PDF from the server documents directory, extract plain text
  2. Chunking  — split text into overlapping segments for retrieval
  3. Embedding — turn each chunk into a vector (HuggingFace embeddings)
  4. Store     — save vectors + text + metadata in the vector DB (Chroma)

Each run also writes a structured log under Logs/indexing/<timestamp>_<filename>.log
"""

import io
import time
import uuid
from pathlib import Path

import chromadb
from fastapi import HTTPException
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
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


def _bad_request(msg: str) -> None:
    raise HTTPException(status_code=400, detail=msg)


async def index_document() -> dict:
    """
    Run loading → chunking → embedding → store for all PDFs inside the server documents folder.
    Returns {"status": "success", "chunks": <int>}.
    """

    source_path = Path(settings.server_documents_dir)

    if source_path.exists() and source_path.is_file():
        pdf_paths = [source_path]
    else:
        source_path.mkdir(parents=True, exist_ok=True)
        pdf_paths = sorted([path for path in source_path.glob("*.pdf") if path.is_file()])

    if not pdf_paths:
        _bad_request(
            "No PDF files found in the server documents directory or file path."
        )

    if not settings.google_api_key:
        err = HTTPException(status_code=400, detail="Add gemnai_key (Gemini API Key) in backend/.env.local")
        logger = get_indexing_logger("server-documents")
        log_pipeline_error(logger, "Stage 3 · Embedding — API key check", err, time.monotonic())
        raise err

    client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
    collection = client.get_or_create_collection(name=settings.collection_name)
    total_chunks = 0

    for pdf_path in pdf_paths:
        filename = pdf_path.name
        logger = get_indexing_logger(filename)
        start = log_pipeline_start(logger, filename)

        raw_bytes = pdf_path.read_bytes()
        reader = PdfReader(io.BytesIO(raw_bytes))
        pages_text = [page.extract_text() or "" for page in reader.pages]
        full_text = "\n".join(pages_text)

        log_before_chunks(logger, filename, len(raw_bytes), len(pages_text), full_text)

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.index_chunk_size,
            chunk_overlap=settings.index_chunk_overlap,
            separators=["\n\n", "\n", " ", ""],
        )
        chunks: list[str] = splitter.split_text(full_text)
        log_after_chunks(logger, chunks, settings.index_chunk_size, settings.index_chunk_overlap)

        documents = [
            Document(page_content=chunk, metadata={"source": filename, "chunk_index": i})
            for i, chunk in enumerate(chunks)
        ]

        try:
            embeddings = HuggingFaceEmbeddings(
                model_name=settings.index_embedding_model,
            )
            vectors: list[list[float]] = embeddings.embed_documents(
                [d.page_content for d in documents]
            )
            vector_dim = len(vectors[0]) if vectors else 0
            log_embedding(
                logger,
                settings.index_embedding_model,
                len(chunks),
                vector_dim,
            )
            log_vectors_table(logger, vectors)

            collection.add(
                ids=[str(uuid.uuid4()) for _ in documents],
                embeddings=vectors,
                documents=[d.page_content for d in documents],
                metadatas=[d.metadata for d in documents],
            )
            log_chroma_stored(
                logger,
                collection_name=settings.collection_name,
                persist_dir=settings.chroma_persist_dir,
                num_docs=len(documents),
                collection=collection,
            )
        except Exception as exc:
            log_pipeline_error(logger, "Embedding or Chroma store", exc, start)
            _bad_request("Indexing failed — check your API key and try again.")

        log_pipeline_end(logger, filename, len(documents), start)
        total_chunks += len(documents)

    return {"status": "success", "chunks": total_chunks}
