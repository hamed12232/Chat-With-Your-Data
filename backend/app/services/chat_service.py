"""
Chat service — four-step RAG pipeline (`rag_answer` / `get_answer`):

  1. Embed   → vectorise the user query (same model as indexing by default)
  2. Retrieve → query Chroma for the top-k most similar chunks
  3. Context → join relevant chunks into a single context block
  4. Generate → call GPT-4o and return the full answer
"""

import chromadb
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from app.core.config import settings

_SYSTEM_PROMPT = (
    "You are a helpful assistant. Answer the user's question "
    "using ONLY the context provided. If the answer is not "
    "in the context, say: I don't know based on the provided documents."
)


async def rag_answer(question: str) -> str:
    """Run the four-step RAG pipeline and return the model answer."""
    # Step 1 — Embed: turn the user question into a vector for similarity search.
    embeddings = OpenAIEmbeddings(
        model=settings.index_embedding_model,
        openai_api_key=settings.openai_api_key,  # type: ignore[arg-type]
    )
    query_vector: list[float] = embeddings.embed_query(question)

    # Step 2 — Retrieve: fetch the top-k most relevant chunks from Chroma.
    client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
    collection = client.get_or_create_collection(name=settings.collection_name)

    results = collection.query(
        query_embeddings=[query_vector],
        n_results=settings.chat_retrieval_top_k,
        include=["documents"],
    )

    relevant_chunks: list[str] = results.get("documents", [[]])[0]

    # Step 3 — Context: concatenate relevant chunks into one prompt block for the LLM.
    context = "Context:\n\n" + "\n\n".join(relevant_chunks)

    # Step 4 — Generate: call the chat model with system prompt + context + question.
    llm = ChatOpenAI(
        model="gpt-4o",
        openai_api_key=settings.openai_api_key,  # type: ignore[arg-type]
    )

    messages = [
        SystemMessage(content=_SYSTEM_PROMPT),
        HumanMessage(content=f"{context}\n\nQuestion: {question}"),
    ]

    response = await llm.ainvoke(messages)
    return str(response.content)


async def get_answer(message: str) -> str:
    """Alias for :func:`rag_answer` (same return value)."""
    return await rag_answer(message)
