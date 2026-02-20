from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.document import Document
from app.utils.file_storage import build_storage_path, save_bytes


class DocumentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_document_stub(
        self,
        filename: str,
        file_type: str,
        owner_id: str,
        content_hash: str | None = None,
    ) -> Document:

        doc = Document(
            filename=filename,
            file_type=file_type,
            uploaded_at=datetime.utcnow(),
            status="uploaded",
            owner_id=owner_id,
            content_hash=content_hash,
        )

        self.db.add(doc)
        await self.db.commit()
        await self.db.refresh(doc)

        return doc

    async def get_by_owner_and_hash(self, owner_id: str, content_hash: str) -> Document | None:
        stmt = (
            select(Document)
            .where(
                Document.owner_id == owner_id,
                Document.content_hash == content_hash
            )
            .order_by(Document.uploaded_at.desc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def save_file(self, doc: Document, original_filename: str, content: bytes) -> None:
        """
        Saves file to disk and updates storage_path.
        """
        storage_path = build_storage_path(doc.id, original_filename)
        save_bytes(storage_path, content)

        doc.storage_path = storage_path

        await self.db.commit()
        await self.db.refresh(doc)
