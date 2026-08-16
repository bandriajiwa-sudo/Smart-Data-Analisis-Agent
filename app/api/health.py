from fastapi import APIRouter
from app.core.config import settings

router = APIRouter()

@router.get("/health")
async def health_check():
    """Endpoint simplistik monitoring HTTP."""
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "services": {
            "llm_api": "connected", # assuming connected normally
            "pos_database": "read_only"
        }
    }
