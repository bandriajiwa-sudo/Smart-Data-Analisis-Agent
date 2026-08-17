import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field
from app.agent.state import AgentState
from app.core.config import settings

logger = logging.getLogger(__name__)

class IntentResponse(BaseModel):
    intent: str = Field(description="Klasifikasi intent: database_query | data_analysis | general_chat")

def node_intent_router(state: AgentState) -> dict:
    """Klasifikasi intent menggunakan LLM native JSON"""
    messages = state.messages
    if not messages:
        return {"intent": "general_chat"}
        
    last_message = messages[-1].content if hasattr(messages[-1], "content") else str(messages[-1])
    
    prompt = (
        "Anda adalah router cerdas. Klasifikasikan intent dari pesan pengguna berikut:\n"
        "1. 'database_query': Meminta data operasional spesifik dari sistem (contoh: penjualan, inventory)\n"
        "2. 'data_analysis': Meminta analisis komparatif atau agregasi lanjutan (contoh: tren bulan lalu)\n"
        "3. 'general_chat': Sapaan, tanya kabar, atau chit-chat umum tanpa butuh database.\n\n"
        "WAJIB OUTPUT HANYA JSON MURNI { \"intent\": \"nama_intent_disini\" } TANPA BLOCK MARKDOWN (TANPA ```json)!!!\n"
        f"Pesan User: {last_message}"
    )
    
    try:
        import json
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", api_key=settings.GEMINI_API_KEY)
        result = llm.invoke(prompt)
        text = result.content.strip().replace("```json", "").replace("```", "").strip()
        parsed = json.loads(text)
        intent = parsed.get("intent", "general_chat")
        
        if intent not in ["database_query", "data_analysis", "general_chat"]:
            intent = "general_chat"
            
        logger.info(f"Routed intent: {intent}")
        return {"intent": intent, "retry_count": 0, "status": "processing"}
    except Exception as e:
        logger.error(f"Router error: {e}")
        return {"intent": "general_chat", "status": "processing"}
