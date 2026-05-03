from fastapi import APIRouter
from pydantic import BaseModel

from app.services.chat_service import answer_question

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[str] = []


@router.post("/", response_model=ChatResponse)
async def chat(body: ChatRequest):
    """Demo: returns a placeholder from `chat_service.answer_question`."""
    return await answer_question(body.question)
