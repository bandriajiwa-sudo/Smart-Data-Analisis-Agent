import logging
import httpx
import asyncio
from fastapi import APIRouter, BackgroundTasks, Request
from app.core.config import settings
from app.api.agent import create_agent_graph
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

logger = logging.getLogger(__name__)
router = APIRouter()

async def dispatch_telegram_message(chat_id: int, message: str):
    """W6++: Kirim hasil agen AI kembali ke handphone Telegram user."""
    token = getattr(settings, "TELEGRAM_BOT_TOKEN", None)
    if not token or token == "dummy":
        logger.error("TELEGRAM_BOT_TOKEN blm diset. Ngga bisa bales chat ke telegram!")
        return
        
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}
    
    # Retry mechanism backoff W6
    retry_delays = [5, 15, 60]
    async with httpx.AsyncClient() as client:
        for attempt, delay in enumerate(retry_delays + [0], 1):
            try:
                resp = await client.post(url, json=payload, timeout=20.0)
                if resp.status_code == 200:
                    logger.info(f"Pesan balesan sukses dikirim ke Telegram Chat ID: {chat_id}")
                    return
            except Exception as e:
                logger.error(f"Gagal membalas Telegram attempt {attempt}: {e}")
            if attempt <= len(retry_delays):
                await asyncio.sleep(delay)

async def run_agent_for_telegram(chat_id: int, text_message: str):
    """Pipa orchestrator asinkron yang menjembatani LangGraph dan Telegram API"""
    # Kirim loading message dulu biar UX Telegram bagus
    await dispatch_telegram_message(chat_id, "⚙️ Sedang mengumpulkan dan memproses instruksi analisa AHASS Anda, mohon tunggu sebentar... ⏳")
    
    async with AsyncPostgresSaver.from_conn_string(settings.CHECKPOINTER_DB_URI) as checkpointer:
        app_graph = await create_agent_graph(checkpointer)
        
        # Kita kunci thread memory session pake Chat ID Telegram! Murni per Room Chat.
        state_input = {
            "thread_id": str(chat_id),
            "user_id": str(chat_id),
            "messages": [("user", text_message)],
            "retry_count": 0 
        }
        
        config = {"configurable": {"thread_id": str(chat_id)}}
        
        try:
            final_state = await app_graph.ainvoke(state_input, config=config)
            answer = final_state.get("final_answer", "Maaf, sistem server AI lagi skip nerespon.")
            await dispatch_telegram_message(chat_id, answer)
        except Exception as e:
            logger.error(f"Telegram execution blocker error di Thread {chat_id}: {e}")
            await dispatch_telegram_message(chat_id, f"Oops bro, LangGraph-nya ngecrash: {e}")

@router.post("/webhook")
async def telegram_webhook_handler(request: Request, background_tasks: BackgroundTasks):
    """Pintu gerbang penampung pesan incoming dr API Telegram (Harus kena public URL/Railway/Ngrok)"""
    try:
        data = await request.json()
        
        # Ekstrak elemen teks 
        if "message" in data and "text" in data["message"]:
            chat_id = data["message"]["chat"]["id"]
            pesan_teks = data["message"]["text"]
            
            # Oper ke _Background Worker_ (Langgraph processing engine) 
            # supaya server dapet bales ke Telegram instantly bahwa 'Pesan udah diterima'
            background_tasks.add_task(run_agent_for_telegram, chat_id, pesan_teks)
            
        return {"ok": True}
    except Exception as e:
        logger.error(f"Gagal nge-parse json Telegram: {e}")
        return {"ok": False, "error": str(e)}
