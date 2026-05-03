from fastapi import APIRouter
from pydantic import AliasChoices, BaseModel, Field

from app.services.chat_service import rag_answer

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    """User text; JSON may use ``message`` or ``question``."""

    message: str = Field(
        ...,
        validation_alias=AliasChoices("message", "question"),
    )


class ChatResponse(BaseModel):
    answer: str


@router.post("/", response_model=ChatResponse)
async def chat(body: ChatRequest) -> ChatResponse:
    """
    Run the RAG retrieval pipeline and return the GPT-4o answer.

    Accepts:  { "message": "..." } or { "question": "..." }
    Returns:  { "answer": "..." }
    """
    answer = await rag_answer(body.message)
    return ChatResponse(answer=answer)
