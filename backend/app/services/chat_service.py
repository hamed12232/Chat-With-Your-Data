"""
Chat service — retrieval + LLM (stub for demo / tutorial builds).
"""


async def answer_question(question: str) -> dict:
    _ = question
    return {
        "answer": (
            "This is a demo reply. Hook up Chroma retrieval and your chat model "
            "in `chat_service.py` when you are ready."
        ),
        "sources": [],
    }
