from pydantic import BaseModel, Field
from typing import List, Optional


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)
    document_ids: Optional[List[int]] = None


class AskResponse(BaseModel):
    answer: str

    class Source(BaseModel):
        citation: int
        chunk_id: int
        document_id: int
        filename: str
        chunk_index: int
        excerpt: str

    sources: List[Source]
