import logging
from fastapi import FastAPI
from app.core.config import settings
from app.api.health import router as health_router
from app.api.agent import router as agent_router

logging.basicConfig(level=logging.INFO, format="%(levelname)s:     %(message)s")

app = FastAPI(title=settings.PROJECT_NAME, version=settings.VERSION, description="Non-Invasive API AI Cognitive Layer")

app.include_router(health_router, prefix="/api/v1", tags=["Operational"])
app.include_router(agent_router, prefix="/api/v1", tags=["AI Core"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
