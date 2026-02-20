from typing import List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chunk import Chunk
from app.models.document import Document
from app.utils.embeddings import embed_text


class RetrievalService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def search(
        self,
        query: str,
        owner_id: str,
        top_k: int = 5,
        document_ids: Optional[List[int]] = None,
    ) -> List[Tuple[Chunk, str, float]]:

        query_embedding = await embed_text(query)

        filters = [
            Chunk.embedding.isnot(None),
            Document.owner_id == owner_id,
        ]
        if document_ids:
            filters.append(Document.id.in_(document_ids))

        stmt = (
            select(
                Chunk,
                Document.filename,
                Chunk.embedding.cosine_distance(query_embedding).label("distance"),
            )
            .join(Document, Chunk.document_id == Document.id)
            .where(*filters)
            .order_by(Chunk.embedding.cosine_distance(query_embedding))
            .limit(top_k)
        )

        result = await self.db.execute(stmt)
        return result.all()
