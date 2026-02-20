import re
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
        sources_by_citation = {}

        for i, (chunk, filename, _distance) in enumerate(results, start=1):
            context_blocks.append(
                f"[{i}] (chunk_id={chunk.id}, document_id={chunk.document_id}, filename={filename}, chunk_index={chunk.chunk_index})\n{chunk.content}"
            )
            sources_by_citation[i] = {
                "citation": i,
                "chunk_id": chunk.id,
                "document_id": chunk.document_id,
                "filename": filename,
                "chunk_index": chunk.chunk_index,
                "excerpt": chunk.content[:240]
            }

        context = "\n\n".join(context_blocks)

        answer = await generate_answer(
            question=question,
            context=context
        )

        cited_numbers = set()
        for value in re.findall(r"\[(\d+)\]", answer):
            citation = int(value)
            if citation in sources_by_citation:
                cited_numbers.add(citation)

        if not cited_numbers:
            # Fallback: expose retrieved chunks if model missed citations.
            cited_numbers = set(sources_by_citation.keys())

        sources = [
            sources_by_citation[citation]
            for citation in sorted(cited_numbers)
        ]

        return {
            "answer": answer,
            "sources": sources
        }
