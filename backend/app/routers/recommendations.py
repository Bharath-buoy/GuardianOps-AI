"""AI recommendation feed endpoint."""
from fastapi import APIRouter, Query

from app.services.mock_data import store

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


@router.get("")
async def get_recommendations(limit: int = Query(default=50, le=200)):
    items = store.get_recommendations(limit=limit)
    return {"total": len(store.recommendations), "recommendations": items}
