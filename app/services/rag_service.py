from typing import List
from app.services.retrieval_service import RetrievalService
from app.utils.llm import generate_answer


class RAGService:
    def __init__(self, db):
        self.retrieval = RetrievalService(db)

    async def ask(self, question: str, owner_id: str, top_k: int = 5):

        results = await self.retrieval.search(
            query=question,
            owner_id=owner_id,
            top_k=top_k
        )

        if not results:
            return {
                "answer": "No relevant information found.",
                "sources": []
            }

        context_blocks = []
        source_ids = []

        for chunk, _distance in results:
            context_blocks.append(chunk.content)
            source_ids.append(chunk.id)

        context = "\n\n".join(context_blocks)

        answer = await generate_answer(
            question=question,
            context=context
        )

        return {
            "answer": answer,
            "sources": source_ids
        }
