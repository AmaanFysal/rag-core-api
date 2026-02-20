from pydantic import BaseModel, Field
from typing import List


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1)
    owner_id: str
    top_k: int = Field(default=5, ge=1, le=20)


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
