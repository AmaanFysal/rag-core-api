from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.document_service import DocumentService
from app.services.processing_service import ProcessingService

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    owner_id: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    document_service = DocumentService(db)
    processing_service = ProcessingService(db)

    doc = await document_service.create_document_stub(
        filename=file.filename,
        file_type=file.filename.split(".")[-1],
        owner_id=owner_id
    )

    await document_service.save_file(doc, file)

    await processing_service.process_document(doc)

    return {
        "document_id": doc.id,
        "status": doc.status,
        "owner_id": doc.owner_id
    }
