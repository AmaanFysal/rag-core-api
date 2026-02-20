from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.core.limiter import limiter
from app.db.session import get_db
from app.services.document_service import DocumentService
from app.services.processing_service import ProcessingService
from app.utils.file_storage import sha256_bytes

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("/")
async def list_documents(
    owner_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = DocumentService(db)
    docs = await service.list_by_owner(owner_id)
    return [{"id": d.id, "filename": d.filename, "status": d.status} for d in docs]


@router.get("/{doc_id}/content", response_class=PlainTextResponse)
async def get_document_content(
    doc_id: int,
    owner_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = DocumentService(db)
    docs = await service.list_by_owner(owner_id)
    doc = next((d for d in docs if d.id == doc_id), None)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if not doc.storage_path:
        raise HTTPException(status_code=404, detail="File not stored")
    path = Path(doc.storage_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")
    return path.read_text(errors="replace")


@router.post("/upload")
@limiter.limit("10/minute")
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    owner_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    document_service = DocumentService(db)
    processing_service = ProcessingService(db)
    original_filename = file.filename or "uploaded_file"
    file_type = original_filename.split(".")[-1]
    content = await file.read()
    content_hash = sha256_bytes(content)

    existing_doc = await document_service.get_by_owner_and_hash(
        owner_id=owner_id,
        content_hash=content_hash
    )

    if existing_doc:
        return {
            "document_id": existing_doc.id,
            "status": existing_doc.status,
            "owner_id": existing_doc.owner_id,
            "deduplicated": True
        }

    doc = await document_service.create_document_stub(
        filename=original_filename,
        file_type=file_type,
        owner_id=owner_id,
        content_hash=content_hash,
    )

    await document_service.save_file(doc, original_filename, content)

    await processing_service.process_document(doc)

    return {
        "document_id": doc.id,
        "status": doc.status,
        "owner_id": doc.owner_id,
        "deduplicated": False
    }
