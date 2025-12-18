from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field, validator


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=500)
    max_results: int = Field(5, ge=1, le=10)

    @validator("query")
    def strip_query(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("query must not be empty")
        return s


class Product(BaseModel):
    sku: str
    name: str
    category: List[str]
    uri: Optional[str]
    msrp: Optional[float]
    final_price: Optional[float]
    release_date: Optional[str]
    in_stock: Optional[bool]
    description: Optional[str]
    score: Optional[float] = None


class SearchMetadata(BaseModel):
    execution_time_ms: float
    cache_hit: bool
    total_index_size: int
    k: int
    results_count: int


class SearchResponse(BaseModel):
    products: List[Product]
    summary: str
    metadata: SearchMetadata
