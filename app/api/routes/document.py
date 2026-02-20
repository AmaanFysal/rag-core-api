from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.document_service import DocumentService
from app.services.processing_service import ProcessingService
from app.utils.file_storage import sha256_bytes

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    owner_id: str = Form(...),
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
