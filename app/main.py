import logging
import uuid
from fastapi import FastAPI, Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.core.config import settings
from app.core.logging_config import setup_structured_logging
from app.api.health import router as health_router
from app.api.agent import router as agent_router

setup_structured_logging()
logger = logging.getLogger(__name__)

# W8: Security Hardening (Rate Limit 10 req/minute)
limiter = Limiter(key_func=get_remote_address, default_limits=["10/minute"])

app = FastAPI(title=settings.PROJECT_NAME, version=settings.VERSION, description="Non-Invasive API AI Cognitive Layer")

# Bind Limiter to App state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# W9: Observability Middleware Scaffold
@app.middleware("http")
async def add_tracing_id(request: Request, call_next):
    trace_id = str(uuid.uuid4())
    logger.info(f"Trace Start [{trace_id}] - {request.method} {request.url.path}")
    response = await call_next(request)
    response.headers["X-Trace-Id"] = trace_id
    logger.info(f"Trace End [{trace_id}] - Status {response.status_code}")
    return response

app.include_router(health_router, prefix="/api/v1", tags=["Operational"])
app.include_router(agent_router, prefix="/api/v1", tags=["AI Core"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
