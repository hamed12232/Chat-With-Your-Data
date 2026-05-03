"""
Chat service — four-step RAG retrieval pipeline:
  1. Embed   → vectorise the user query with OpenAI text-embedding-3-small
  2. Retrieve → query Chroma for the top-k most similar chunks
  3. Context → join retrieved chunks into a single context block
  4. Generate → call GPT-4o and return the full answer at once
"""

import chromadb
from fastapi import HTTPException
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.messages import HumanMessage, SystemMessage

from app.core.config import settings
from app.core.chat_logger import (
    get_chat_logger,
    log_chat_start,
    log_embed_query,
    log_retrieve_chunks,
    log_build_context,
    log_generate,
    log_chat_end,
    log_chat_error,
)

# ── System prompt ──────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = (
    "You are a helpful assistant. Answer the user's question "
    "using ONLY the context provided. If the answer is not "
    "in the context, say: I don't know based on the provided documents."
)

_EMBEDDING_MODEL = "text-embedding-3-small"
_CHAT_MODEL      = "gpt-4o"


async def get_answer(message: str) -> str:
    """
    Run the four-step RAG pipeline and return the full answer as a string.
    Each step is logged to Logs/chat/<timestamp>_<query>.log
    """

    logger = get_chat_logger(message)
    start  = log_chat_start(logger, message)

    # ── Step 1/4: Embed query ──────────────────────────────────────────────────
    print("Step 1/4: Embedding query...")

    if not settings.openai_api_key:
        err = HTTPException(status_code=500, detail="OPENAI_API_KEY is not configured.")
        log_chat_error(logger, "1/4 · Embed — missing API key", err, start)
        raise err

    try:
        embeddings   = OpenAIEmbeddings(
            model=_EMBEDDING_MODEL,
            openai_api_key=settings.openai_api_key,  # type: ignore[arg-type]
        )
        query_vector: list[float] = embeddings.embed_query(message)
    except Exception as exc:
        log_chat_error(logger, "1/4 · Embed — API call", exc, start)
        raise HTTPException(status_code=500, detail=f"Embedding failed: {exc}") from exc

    log_embed_query(logger, _EMBEDDING_MODEL, message, query_vector)

    # ── Step 2/4: Retrieve chunks ──────────────────────────────────────────────
    print("Step 2/4: Retrieving chunks...")

    try:
        client     = chromadb.PersistentClient(path=settings.chroma_persist_dir)
        collection = client.get_or_create_collection(name=settings.collection_name)
        results    = collection.query(
            query_embeddings=[query_vector],
            n_results=settings.chat_retrieval_top_k,
            include=["documents", "distances"],
        )
    except Exception as exc:
        log_chat_error(logger, "2/4 · Retrieve — Chroma query", exc, start)
        raise HTTPException(status_code=500, detail=f"Chroma query failed: {exc}") from exc

    # Flatten the nested lists returned by Chroma's query API
    raw_docs: list[str]    = results.get("documents", [[]])[0]
    raw_distances          = results.get("distances", [[]])[0]
    raw_dists: list[float] = [float(d) for d in raw_distances] if raw_distances else []

    # Deduplicate by exact content — keeps the first (lowest-distance) copy
    seen: set[str]          = set()
    retrieved_docs: list[str]  = []
    distances: list[float]     = []
    for doc, dist in zip(raw_docs, raw_dists):
        if doc not in seen:
            seen.add(doc)
            retrieved_docs.append(doc)
            distances.append(dist)

    log_retrieve_chunks(logger, settings.chat_retrieval_top_k, retrieved_docs, distances)

    # Guard: nothing indexed yet
    if not retrieved_docs:
        answer = "No relevant documents found. Please index documents first."
        log_chat_end(logger, start)
        return answer

    # ── Step 3/4: Build context ────────────────────────────────────────────────
    print("Step 3/4: Building context...")

    context = "Context:\n\n" + "\n\n".join(retrieved_docs)

    log_build_context(logger, retrieved_docs, context)

    # ── Step 4/4: Generate ────────────────────────────────────────────────────
    print("Step 4/4: Generating response...")

    try:
        llm = ChatOpenAI(
            model=_CHAT_MODEL,
            temperature=settings.chat_llm_temperature,
            openai_api_key=settings.openai_api_key,  # type: ignore[arg-type]
        )
        messages = [
            SystemMessage(content=_SYSTEM_PROMPT),
            HumanMessage(content=f"{context}\n\nQuestion: {message}"),
        ]
        response = await llm.ainvoke(messages)
        answer   = str(response.content)
    except Exception as exc:
        log_chat_error(logger, "4/4 · Generate — LLM call", exc, start)
        raise HTTPException(status_code=500, detail=f"LLM generation failed: {exc}") from exc

    log_generate(
        logger,
        _CHAT_MODEL,
        settings.chat_llm_temperature,
        _SYSTEM_PROMPT,
        message,
        context,
        answer,
    )
    log_chat_end(logger, start)

    return answer
