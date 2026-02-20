from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.core.limiter import limiter
from app.db.session import get_db
from app.schemas.ask import AskRequest, AskResponse
from app.services.rag_service import RAGService

router = APIRouter(prefix="/ask", tags=["ask"])


@router.post("/", response_model=AskResponse)
@limiter.limit("30/minute")
async def ask_question(
    request: Request,
    payload: AskRequest,
    owner_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = RAGService(db)

    result = await service.ask(
        question=payload.question,
        owner_id=owner_id,
        top_k=payload.top_k
    )

    return result
