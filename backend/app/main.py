import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.routers import chat, index
from app.core.indexing_logger import LOGS_DIR

logger = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(app: FastAPI):
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    logger.info("Indexing logs directory ready → %s", LOGS_DIR.resolve())
    yield

app = FastAPI(
    title="RAG Chatbot API",
    description="Retrieval-Augmented Generation backend powered by LangChain, Chroma, and OpenAI.",
    version="0.1.0",
    lifespan=lifespan,
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


# Log the full validation detail so 422 errors are visible in docker logs
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error("422 Validation error on %s %s → %s", request.method, request.url.path, exc.errors())
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()},
    )


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok"}
