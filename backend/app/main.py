from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import chat, index

app = FastAPI(
    title="RAG Chatbot API",
    description="Retrieval-Augmented Generation backend powered by LangChain, Chroma, and OpenAI.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(index.router)
app.include_router(chat.router)


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok"}
