from fastapi import APIRouter
from pydantic import BaseModel

from app.services.chat_service import get_answer

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str


@router.post("", response_model=ChatResponse)
async def chat(body: ChatRequest) -> ChatResponse:
    """
    Run the RAG retrieval pipeline and return the full GPT-4o answer.

    Accepts:  { "message": "user question here" }
    Returns:  { "reply": "..." }
    """
    reply = await get_answer(body.message)
    return ChatResponse(reply=reply)
