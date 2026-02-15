from typing import List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
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
        top_k: int = 5
    ) -> List[Tuple[Chunk, float]]:

        query_embedding = await embed_text(query)

        stmt = (
            select(
                Chunk,
                Chunk.embedding.cosine_distance(query_embedding).label("distance")
            )
            .join(Document, Chunk.document_id == Document.id)
            .where(
                Chunk.embedding.isnot(None),
                Document.owner_id == owner_id
            )
            .order_by(Chunk.embedding.cosine_distance(query_embedding))
            .limit(top_k)
        )

        result = await self.db.execute(stmt)

        return result.all()
