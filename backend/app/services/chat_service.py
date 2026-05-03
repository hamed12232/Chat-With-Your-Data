"""
Chat service — four-step RAG pipeline (`rag_answer` / `get_answer`):

  1. Embed   → vectorise the user query (same model as indexing by default)
  2. Retrieve → query Chroma for the top-k most similar chunks
  3. Context → join relevant chunks into a single context block
  4. Generate → call GPT-4o and return the full answer

Each chat run may write a structured log under Logs/chat/<timestamp>_<query_slug>.log
"""

import chromadb
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

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

_SYSTEM_PROMPT = (
    "You are a helpful assistant. Answer the user's question "
    "using ONLY the context provided. If the answer is not "
    "in the context, say: I don't know based on the provided documents."
)

_CHAT_MODEL = "gpt-4o"


async def rag_answer(question: str) -> str:
    """Run the four-step RAG pipeline and return the model answer."""
    logger = get_chat_logger(question)
    start = log_chat_start(logger, question)

    try:
        # Step 1 — Embed: turn the user question into a vector for similarity search.
        embeddings = OpenAIEmbeddings(
            model=settings.index_embedding_model,
            openai_api_key=settings.openai_api_key,  # type: ignore[arg-type]
        )
        query_vector: list[float] = embeddings.embed_query(question)
        log_embed_query(logger, settings.index_embedding_model, question, query_vector)

        # Step 2 — Retrieve: fetch the top-k most relevant chunks from Chroma.
        client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
        collection = client.get_or_create_collection(name=settings.collection_name)

        results = collection.query(
            query_embeddings=[query_vector],
            n_results=settings.chat_retrieval_top_k,
            include=["documents", "distances"],
        )

        relevant_chunks: list[str] = results.get("documents", [[]])[0]
        raw_distances = results.get("distances", [[]])[0]
        distances: list[float] | None = (
            [float(d) for d in raw_distances] if raw_distances else None
        )

        log_retrieve_chunks(
            logger,
            settings.chat_retrieval_top_k,
            relevant_chunks,
            distances,
        )

        if not relevant_chunks:
            log_chat_end(logger, start)
            return "No relevant documents found. Please index documents first."

        # Step 3 — Context: concatenate relevant chunks into one prompt block for the LLM.
        context = "Context:\n\n" + "\n\n".join(relevant_chunks)
        log_build_context(logger, relevant_chunks, context)

        # Step 4 — Generate: call the chat model with system prompt + context + question.
        llm = ChatOpenAI(
            model=_CHAT_MODEL,
            openai_api_key=settings.openai_api_key,  # type: ignore[arg-type]
        )

        messages = [
            SystemMessage(content=_SYSTEM_PROMPT),
            HumanMessage(content=f"{context}\n\nQuestion: {question}"),
        ]

        response = await llm.ainvoke(messages)
        answer = str(response.content)
        log_generate(
            logger,
            _CHAT_MODEL,
            _SYSTEM_PROMPT,
            question,
            context,
            answer,
        )
        log_chat_end(logger, start)
        return answer

    except Exception as exc:
        log_chat_error(logger, "chat pipeline", exc, start)
        raise


async def get_answer(message: str) -> str:
    """Alias for :func:`rag_answer` (same return value)."""
    return await rag_answer(message)
