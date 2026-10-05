from pydantic import BaseModel, Field
from typing import Optional

class KnowledgeCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1)
    source: Optional[str] = ""

class SearchRequest(BaseModel):
    query: str = Field(min_length=1)
    limit: int = Field(default=5, ge=1, le=20)

class GenerateRequest(BaseModel):
    query: str = Field(min_length=1)
    limit: int = Field(default=6, ge=1, le=20)
