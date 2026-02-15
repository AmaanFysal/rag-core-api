from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.ask import AskRequest, AskResponse
from app.services.rag_service import RAGService

router = APIRouter(prefix="/ask", tags=["ask"])


@router.post("/", response_model=AskResponse)
async def ask_question(
    request: AskRequest,
    db: AsyncSession = Depends(get_db)
):
    service = RAGService(db)

    result = await service.ask(
        question=request.question,
        owner_id=request.owner_id,
        top_k=request.top_k
    )

    return result
