from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[str] = []


@router.post("/", response_model=ChatResponse)
async def chat(body: ChatRequest):
    """
    Retrieve relevant chunks from Chroma, then generate an answer via GPT-4o.
    Implementation delegated to chat_service.
    """
    raise HTTPException(status_code=501, detail="Not implemented yet")
