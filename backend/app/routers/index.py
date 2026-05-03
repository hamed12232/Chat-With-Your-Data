from fastapi import APIRouter, File, UploadFile
from pydantic import BaseModel

from app.services.index_service import index_document

router = APIRouter(prefix="/index", tags=["index"])


class IndexResponse(BaseModel):
    status: str
    chunks: int


@router.post("", response_model=IndexResponse)
@router.post("/", response_model=IndexResponse)
async def index_documents(file: UploadFile = File(...)):
    return await index_document(file)
