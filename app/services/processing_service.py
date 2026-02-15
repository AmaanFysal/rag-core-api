from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete

from app.models.document import Document
from app.models.chunk import Chunk
from app.utils.text_extraction import extract_text
from app.utils.chunking import chunk_text
from app.utils.embeddings import embed_text



class ProcessingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def process_document(self, doc: Document, chunk_size: int = 1200, overlap: int = 150) -> None:

        doc.status = "processing"
        doc.error_message = None
        await self.db.commit()
        await self.db.refresh(doc)

        try:
            if not doc.storage_path:
                raise ValueError("storage_path is null; file not stored")

            text = extract_text(doc.storage_path, doc.file_type)
            chunks = chunk_text(text, chunk_size=chunk_size, overlap=overlap)

            await self.db.execute(delete(Chunk).where(Chunk.document_id == doc.id))

            for i, content in enumerate(chunks):
                embedding = await embed_text(content)
                self.db.add(Chunk(document_id=doc.id, chunk_index=i, content=content, embedding=embedding))

            doc.status = "ready" if chunks else "failed"
            if not chunks:
                doc.error_message = "No extractable text found"

            await self.db.commit()
            await self.db.refresh(doc)

        except Exception as e:
            doc.status = "failed"
            doc.error_message = str(e)
            await self.db.commit()
            await self.db.refresh(doc)
            raise
