from pydantic import BaseModel, Field
from typing import List


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)


class SearchResult(BaseModel):
    chunk_id: int
    document_id: int
    chunk_index: int
    content: str
    distance: float


class SearchResponse(BaseModel):
    results: List[SearchResult]
