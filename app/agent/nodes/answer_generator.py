import json
import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from app.agent.state import AgentState
from app.core.config import settings

logger = logging.getLogger(__name__)

def node_answer_generator(state: AgentState) -> dict:
    """Format Output Natural Language setelah data terkumpul"""
    messages = state.messages
    last_message = messages[-1].content if hasattr(messages[-1], "content") else str(messages[-1])
    
    if state.status == "error":
        fallback = f"Maaf, saya gagal mengeksekusi instruksi Anda karena kendala backend: {state.error_log}"
        return {"final_answer": fallback, "status": "error"}

    query_res = state.query_result.get("data", []) if state.query_result else []
    # Truncate JSON if needed so it doesn't break token limit.
    subset = query_res[:50]
    data_str = json.dumps(subset)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Anda adalah Asisten Bisnis cerdas dan analis operasional untuk aplikasi POS.\n\n"
                   "Aturan Respon:\n"
                   "1. Jawab langsung secara lugas, profesional, dan ramah selayaknya asisten analis operasional.\n"
                   "2. Jangan gunakan kalimat pembuka klise seperti 'Berdasarkan dataset...' atau 'Berdasarkan data yang tersedia'.\n"
                   "3. Dilarang keras menyebut istilah teknis database/SQL (seperti COALESCE, Query, Table, Column, SELECT) di dalam jawaban Anda.\n"
                   "4. Format angka mata uang ke standar Rupiah yang rapi (contoh: Rp35.000).\n\n"
                   "Dataset Analisis:\n{data}"),
        ("human", "{question}")
    ])
    
    try:
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", api_key=settings.GEMINI_API_KEY)
        chain = prompt | llm
        result = chain.invoke({"data": data_str, "question": last_message})
        return {"final_answer": result.content, "status": "success"}
    except Exception as e:
        logger.error(f"Final Answer Error: {e}")
        # Tangkap 429 Too Many Requests spesifik
        if "429" in str(e) or "Resource exhausted" in str(e):
            return {"final_answer": "Sistem NLP Overload (Limit 8x Request Per Menit gratisan Google habis karena banyak query berturut-turut). Tolong tunggu 1-2 menit sebelum tanya lagi ya bro! ⏳", "status": "error"}
            
        return {"final_answer": f"Terjadi galat HTTP API dari server AI: {str(e)}", "status": "error"}
