from fastapi import FastAPI

from app.routers import chat, index

app = FastAPI(
    title="RAG Chatbot API",
    description="Retrieval-Augmented Generation backend powered by LangChain, Chroma, and Google Gemini.",
    version="0.1.0",
)

app.include_router(index.router)
app.include_router(chat.router)


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok"}
