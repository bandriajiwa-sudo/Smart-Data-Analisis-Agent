import logging
from langchain_groq import ChatGroq
from pydantic import BaseModel, Field
from app.agent.state import AgentState
from app.core.config import settings

logger = logging.getLogger(__name__)

class IntentResponse(BaseModel):
    intent: str = Field(description="Klasifikasi intent: database_query | data_analysis | general_chat")

def node_intent_router(state: AgentState) -> dict:
    """Klasifikasi intent menggunakan LLM Structured Output"""
    messages = state.messages
    if not messages:
        return {"intent": "general_chat"}
        
    last_message = messages[-1].content if hasattr(messages[-1], "content") else str(messages[-1])
    
    prompt = (
        "Anda adalah router cerdas. Klasifikasikan intent dari pesan pengguna berikut:\n"
        "1. 'database_query': Meminta data operasional spesifik dari sistem (contoh: penjualan, inventory)\n"
        "2. 'data_analysis': Meminta analisis komparatif atau agregasi lanjutan (contoh: tren bulan lalu)\n"
        "3. 'general_chat': Sapaan, tanya kabar, atau chit-chat umum tanpa butuh database.\n\n"
        f"Pesan User: {last_message}"
    )
    
    try:
        llm = ChatGroq(model="llama-3.3-70b-versatile", api_key=settings.GROQ_API_KEY)
        structured_llm = llm.with_structured_output(IntentResponse)
        result = structured_llm.invoke(prompt)
        intent = result.intent
        logger.info(f"Routed intent: {intent}")
        return {"intent": intent, "retry_count": 0, "status": "processing"}
    except Exception as e:
        logger.error(f"Router error: {e}")
        return {"intent": "general_chat", "status": "processing"}
