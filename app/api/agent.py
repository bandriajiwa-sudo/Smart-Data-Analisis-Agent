import hmac
import hashlib
import json
import logging
import httpx
import uuid
import asyncio
import re
from typing import Optional
from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends, Request
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel
from app.core.config import settings
from app.agent.graph import create_agent_graph
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

logger = logging.getLogger(__name__)

router = APIRouter()
api_key_header = APIKeyHeader(name="Authorization", auto_error=False)

def verify_api_key(api_key: str = Depends(api_key_header)):
    if not api_key:
        raise HTTPException(status_code=401, detail="API Key is missing")
    token = api_key.replace("Bearer ", "").strip()
    if token != settings.API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized Valid API Key Needed.")
    return token

class ContextModel(BaseModel):
    outlet_id: Optional[str] = None
    timezone: Optional[str] = "Asia/Jakarta"

class AgentRequest(BaseModel):
    user_id: str
    pesan: str
    webhook_url: str
    webhook_secret: Optional[str] = None
    context: Optional[ContextModel] = None

async def dispatch_webhook(url: str, secret: Optional[str], payload: dict):
    """Menghitung SHA256 HMAC & Dispatch webhook event secara Asynchronous (Mendukung Retries)"""
    payload_string = json.dumps(payload, separators=(',', ':'), ensure_ascii=False)
    headers = {"Content-Type": "application/json"}
    
    if secret:
        signature = hmac.new(
            secret.encode('utf-8'),
            payload_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        headers["X-AI-Signature"] = f"sha256={signature}"
        
    retry_delays = [5, 15, 60]  # W6 Exponential Backoff Strategy Phase 2
    
    async with httpx.AsyncClient() as client:
        for attempt, delay in enumerate(retry_delays + [0], 1):
            try:
                resp = await client.post(url, headers=headers, json=payload, timeout=20.0)
                if resp.status_code < 400:
                    logger.info(f"Webhook pushed successfully | Target: {url} | Status: {resp.status_code}")
                    return
                else:
                    logger.warning(f"Webhook failed HTTP {resp.status_code}, attempt {attempt}")
            except Exception as e:
                logger.error(f"Webhook Exception attempt {attempt}: {e}")
                
            if attempt <= len(retry_delays):
                logger.info(f"Retrying webhook to {url} in {delay} seconds...")
                await asyncio.sleep(delay)
                
    logger.critical(f"Webhook permanently failed after {len(retry_delays)} retries! Payload dropped.")

async def run_agent_and_dispatch_webhook(payload: AgentRequest):
    """
    Background worker function to run Graph Agent and send final result to external Webhook 
    with HMAC-SHA256 signature and Exponential Backoff Retry.
    """
    logger.info(f"Background worker started for User: {payload.user_id}")
    
    async with AsyncPostgresSaver.from_conn_string(settings.CHECKPOINTER_DB_URI) as checkpointer:
        app_graph = await create_agent_graph(checkpointer)
        
        state_input = {
            "thread_id": payload.user_id,
            "user_id": payload.user_id,
            "messages": [("user", payload.pesan)],
            "retry_count": 0
        }
        
        config = {"configurable": {"thread_id": payload.user_id}}
        
        try:
            final_state = await app_graph.ainvoke(state_input, config=config)
            
            out_payload = {
                "user_id": final_state.get("thread_id"),
                "status": final_state.get("status", "unknown"),
                "answer": final_state.get("final_answer", None),
                "error_log": final_state.get("error_log", None),
                "sql_used": final_state.get("generated_sql", None)
            }
            
            await dispatch_webhook(payload.webhook_url, payload.webhook_secret, out_payload)
            
        except Exception as e:
            logger.error(f"LangGraph execution exception on Thread {payload.user_id}: {e}")
            error_payload = {
                "user_id": payload.user_id,
                "status": "fatal_error",
                "message": str(e)
            }
            await dispatch_webhook(payload.webhook_url, payload.webhook_secret, error_payload)
            logger.info("Checkpointer db_pool successfully closed.")

def sanitize_input(text: str) -> str:
    """W8: Input Sanitization menolak raw byte executable & karakter unicode ilegal."""
    clean_text = re.sub(r'[^\w\s\?\.,!:\'"/-]', '', text)
    return clean_text.strip()

@router.post("/run-agent", status_code=202)
async def trigger_agent(req: AgentRequest, request: Request, background_tasks: BackgroundTasks, _token: str = Depends(verify_api_key)):
    job_id = str(uuid.uuid4())
    req.pesan = sanitize_input(req.pesan)  # W8 Sanitization applied
    
    background_tasks.add_task(run_agent_and_dispatch_webhook, req)
    
    return {
        "success": True,
        "data": {
            "job_id": job_id,
            "status": "processing",
            "thread_id": req.user_id,
            "message": "AI Task Queued for Processing"
        }
    }
