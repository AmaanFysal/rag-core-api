import os
from datetime import datetime
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document


UPLOAD_DIR = "uploads"


class DocumentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_document_stub(
        self,
        filename: str,
        file_type: str,
        owner_id: str,
    ) -> Document:

        doc = Document(
            filename=filename,
            file_type=file_type,
            uploaded_at=datetime.utcnow(),
            status="uploaded",
            owner_id=owner_id,
        )

        self.db.add(doc)
        await self.db.commit()
        await self.db.refresh(doc)

        return doc

    async def save_file(self, doc: Document, file: UploadFile) -> None:
        """
        Saves file to disk and updates storage_path.
        """

        os.makedirs(UPLOAD_DIR, exist_ok=True)

        storage_path = os.path.join(
            UPLOAD_DIR,
            f"{doc.id}_{file.filename}"
        )

        with open(storage_path, "wb") as f:
            content = await file.read()
            f.write(content)

        doc.storage_path = storage_path

        await self.db.commit()
        await self.db.refresh(doc)
