from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List

router = APIRouter(prefix="/index", tags=["index"])


@router.post("/")
async def index_documents(files: List[UploadFile] = File(...)):
    """
    Accept one or more uploaded files, chunk, embed, and store them in Chroma.
    Implementation delegated to index_service.
    """
    raise HTTPException(status_code=501, detail="Not implemented yet")
