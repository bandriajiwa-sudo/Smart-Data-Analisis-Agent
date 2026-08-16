import hmac
import hashlib
import json
import logging
import httpx
import uuid
from typing import Optional
from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel
from app.core.config import settings
from app.agent.graph import create_agent_graph

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

def dispatch_webhook(url: str, secret: Optional[str], payload: dict):
    """Menghitung SHA256 HMAC & Dispatch webhook event"""
    payload_string = json.dumps(payload, separators=(',', ':'), ensure_ascii=False)
    headers = {"Content-Type": "application/json"}
    
    if secret:
        signature = hmac.new(
            secret.encode('utf-8'),
            payload_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        headers["X-AI-Signature"] = f"sha256={signature}"
        
    try:
        with httpx.Client() as client:
            resp = client.post(url, headers=headers, json=payload, timeout=20.0)
            logger.info(f"Webhook pushed | Target: {url} | Status: {resp.status_code}")
    except Exception as e:
        logger.error(f"Webhook Delivery Failed (Silent drop via BackgroundTask): {e}")

async def run_agent_and_dispatch_webhook(payload: dict):
    # 1. Bangun / Compile LangGraph execution graph
    app_graph = create_agent_graph()
    
    state_input = {
        "thread_id": payload["user_id"], 
        "user_id": payload["user_id"],
        "messages": [("user", payload["pesan"])]
    }
    
    config = {"configurable": {"thread_id": payload["user_id"]}}
    
    try:
        # Trigger event async invocation agent (LLM, RDBMS, dst)
        final_state = await app_graph.ainvoke(state_input, config=config)
        out_payload = {
            "event": "agent.completed",
            "user_id": payload["user_id"],
            "status": final_state.get("status", "error"),
            "data": {
                "answer": final_state.get("final_answer"),
                "intent": final_state.get("intent"),
                "error": final_state.get("error_log")
            }
        }
    except Exception as e:
        logger.error(f"Graph Invocation Exception Crash: {e}")
        out_payload = {
            "event": "agent.completed",
            "user_id": payload["user_id"],
            "status": "error",
            "data": {"error": str(e)}
        }
        
    # 3. Fire Post-Dispatch (keluarkan dari mesin AI menuju backend utama user)
    dispatch_webhook(payload["webhook_url"], payload.get("webhook_secret"), out_payload)

@router.post("/run-agent", status_code=202)
async def trigger_agent(req: AgentRequest, background_tasks: BackgroundTasks, _token: str = Depends(verify_api_key)):
    job_id = str(uuid.uuid4())
    payload = req.model_dump()
    
    background_tasks.add_task(run_agent_and_dispatch_webhook, payload)
    
    return {
        "success": True,
        "data": {
            "job_id": job_id,
            "status": "processing",
            "thread_id": req.user_id,
            "message": "AI Task Queued for Processing"
        }
    }
