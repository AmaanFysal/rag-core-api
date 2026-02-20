from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.core.limiter import limiter
from app.db.session import get_db
from app.schemas.search import SearchRequest, SearchResponse
from app.services.retrieval_service import RetrievalService

router = APIRouter(prefix="/search", tags=["search"])


@router.post("/", response_model=SearchResponse)
@limiter.limit("30/minute")
async def search_documents(
    request: Request,
    payload: SearchRequest,
    owner_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = RetrievalService(db)

    results = await service.search(
        query=payload.query,
        owner_id=owner_id,
        top_k=payload.top_k
    )

    return {
        "results": [
            {
                "chunk_id": chunk.id,
                "document_id": chunk.document_id,
                "chunk_index": chunk.chunk_index,
                "content": chunk.content,
                "distance": float(distance)
            }
            for chunk, distance in results
        ]
    }
