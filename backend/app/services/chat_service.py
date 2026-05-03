"""
Chat service — four-step RAG retrieval pipeline:
  1. Embed   → vectorise the user query with OpenAI text-embedding-3-small
  2. Retrieve → query Chroma for the top-k most similar chunks
  3. Context → join retrieved chunks into a single context block
  4. Generate → call GPT-4o and return the full answer at once
"""

import chromadb
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.messages import HumanMessage, SystemMessage

from app.core.config import settings

# ── System prompt ──────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = (
    "You are a helpful assistant. Answer the user's question "
    "using ONLY the context provided. If the answer is not "
    "in the context, say: I don't know based on the provided documents."
)


async def get_answer(message: str) -> str:
    """
    Run the four-step RAG pipeline and return the full answer as a string.
    """

    # ── Step 1/4: Embed query ──────────────────────────────────────────────────
    print("Step 1/4: Embedding query...")

    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small",
        openai_api_key=settings.openai_api_key,  # type: ignore[arg-type]
    )
    query_vector: list[float] = embeddings.embed_query(message)

    # ── Step 2/4: Retrieve chunks ──────────────────────────────────────────────
    print("Step 2/4: Retrieving chunks...")

    client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
    collection = client.get_or_create_collection(name=settings.collection_name)

    results = collection.query(
        query_embeddings=[query_vector],
        n_results=settings.chat_retrieval_top_k,
        include=["documents"],
    )

    # Flatten the nested list returned by Chroma's query API
    retrieved_docs: list[str] = results.get("documents", [[]])[0]

    # Guard: nothing indexed yet
    if not retrieved_docs:
        return "No relevant documents found. Please index documents first."

    # ── Step 3/4: Build context ────────────────────────────────────────────────
    print("Step 3/4: Building context...")

    context = "Context:\n\n" + "\n\n".join(retrieved_docs)

    # ── Step 4/4: Generate ────────────────────────────────────────────────────
    print("Step 4/4: Generating response...")

    llm = ChatOpenAI(
        model="gpt-4o",
        openai_api_key=settings.openai_api_key,  # type: ignore[arg-type]
    )

    messages = [
        SystemMessage(content=_SYSTEM_PROMPT),
        HumanMessage(content=f"{context}\n\nQuestion: {message}"),
    ]

    response = await llm.ainvoke(messages)
    return str(response.content)
