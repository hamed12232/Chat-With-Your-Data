from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.services.index_service import index_document

router = APIRouter(prefix="/index", tags=["index"])


class IndexResponse(BaseModel):
    status: str
    chunks: int


# Two routes so both /index and /index/ work without a 307 redirect
@router.post("", response_model=IndexResponse)
@router.post("/", response_model=IndexResponse, include_in_schema=False)
async def index_documents(request: Request):
    """
    Accept a single PDF upload (multipart/form-data).
    The file field may be named 'file' or 'files'.
    """
    # Parse the multipart form directly from the raw request so we are not
    # sensitive to the exact FastAPI parameter-binding path.
    try:
        form = await request.form()
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Could not parse multipart form: {exc}. "
                   "Make sure the request Content-Type is multipart/form-data "
                   "and that no manual Content-Type header overrides the boundary.",
        ) from exc

    # Accept either 'file' or 'files' as the field name
    upload = form.get("file") or form.get("files")

    if upload is None:
        available = list(form.keys())
        raise HTTPException(
            status_code=400,
            detail=f"No file field found. Fields received: {available}. "
                   "Expected a field named 'file' of type File.",
        )

    result = await index_document(upload)  # type: ignore[arg-type]
    return result
