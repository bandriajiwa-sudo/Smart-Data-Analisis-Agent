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
        "Anda adalah router klasifikasi intent untuk sistem bengkel AHASS (Jasa Service & Sparepart Motor Honda).\n"
        "Tugasmu HANYA mengklasifikasi pesan user ke SATU dari tiga kategori:\n\n"
        "1. 'database_query' - PILIH INI jika user bertanya tentang:\n"
        "   - Transaksi, penjualan, omset, pendapatan, total, jumlah\n"
        "   - Jasa, service, servis, ganti oli, tune up\n"
        "   - Sparepart, suku cadang, produk, barang, stok, inventory\n"
        "   - Pelanggan, customer, motor, kendaraan\n"
        "   - Data hari ini, minggu ini, bulan ini, tahun ini\n"
        "   - Laporan, rekap, daftar, list\n"
        "   - Berapa, ada berapa, total berapa, yang mana, apa saja\n\n"
        "2. 'data_analysis' - PILIH INI jika user minta PERBANDINGAN atau TREN:\n"
        "   - Contoh: 'bandingkan penjualan bulan lalu dengan bulan ini'\n"
        "   - Contoh: 'tren penjualan 3 bulan terakhir'\n\n"
        "3. 'general_chat' - PILIH INI HANYA jika pesan BUKAN tentang data/bisnis:\n"
        "   - Contoh: 'halo', 'apa kabar', 'terima kasih', 'siapa kamu'\n\n"
        "PENTING: Jika RAGU antara database_query dan general_chat, SELALU pilih database_query!\n\n"
        "OUTPUT HANYA JSON MURNI: {\"intent\": \"nama_intent\"}\n"
        "DILARANG pakai markdown atau backticks!\n\n"
        f"Pesan User: {last_message}"
    )
    
    try:
        import json
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(
            model="nvidia/nemotron-3.5-lightning:free", 
            api_key=settings.OPENROUTER_API_KEY, 
            base_url="https://openrouter.ai/api/v1"
        )
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
