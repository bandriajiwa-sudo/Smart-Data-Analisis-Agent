import json
import logging
from langchain_groq import ChatGroq
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
        ("system", "Anda adalah Asisten Bisnis cerdas bagi toko berbasis aplikasi POS.\n"
                   "Berdasarkan dataset query berikut ini, berikan rangkuman profesional untuk menjawab pertanyaan.\n\n"
                   "Dataset Analisis:\n{data}"),
        ("human", "{question}")
    ])
    
    try:
        llm = ChatGroq(model="llama-3.3-70b-versatile", api_key=settings.GROQ_API_KEY)
        chain = prompt | llm
        result = chain.invoke({"data": data_str, "question": last_message})
        return {"final_answer": result.content, "status": "success"}
    except Exception as e:
        logger.error(f"Final Answer Error: {e}")
        return {"final_answer": "Terjadi galat (error) di dalam sistem NLP kami saat memformulasikan respon akhir.", "status": "error"}
