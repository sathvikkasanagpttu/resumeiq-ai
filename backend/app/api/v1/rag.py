from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.rag.retriever import rag_retriever
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter()

@router.get("/search")
def search_knowledge_base(
    q: str = Query(..., description="Query terms or skill"),
    category: Optional[str] = Query(None, description="Optional category filter"),
    top_k: int = Query(4, ge=1, le=10),
    current_user: User = Depends(get_current_user)
):
    results = rag_retriever.hybrid_search(query=q, category=category, top_k=top_k)
    return {"query": q, "category": category, "count": len(results), "results": results}
