import logging
from langchain_core.prompts import ChatPromptTemplate
from app.agent.state import AgentState
from app.core.config import settings

logger = logging.getLogger(__name__)

from app.db.introspection import fetch_database_schema

async def node_sql_generator(state: AgentState) -> dict:
    """Menghasilkan raw SQL query berdasarkan intent (Dynamic Schema)"""
    SCHEMA_CONTEXT = await fetch_database_schema()
    if not SCHEMA_CONTEXT:
        SCHEMA_CONTEXT = "Table: sales\\nColumns: id, total"
    if state.intent == "general_chat":
        return {}

    messages = state.messages
    last_message = messages[-1].content if hasattr(messages[-1], "content") else str(messages[-1])
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Anda adalah PostgreSQL Data Analyst cerdas untuk sistem bengkel dan toko AHASS (Jasa Service & Sparepart).\n"
                   "Buat satu baris query postgres untuk menjawab input user.\n"
                   "DILARANG menulis markdown, DILARANG memberi penjelasan. HANYA OUTPUTKAN RAW PURE SQL.\n"
                   f"Skema Database:\n{SCHEMA_CONTEXT}\n\n"
                   "--- CONTOH ATURAN & FEW-SHOT EXAMPLES ---\n"
                   "1. Jika user bertanya 'transaksi jasa' atau 'service', carilah tabel yang berhubungan dengan services, job_orders, atau transactions yang memiliki tipe jasa.\n"
                   "2. Jika user bertanya 'suku cadang' atau 'sparepart', carilah relasi product/items.\n"
                   "User: Berapa total penjualan hari ini?\n"
                   "SQL: SELECT COALESCE(SUM(total), 0) FROM sales WHERE DATE(created_at) = CURRENT_DATE;\n\n"
                   "User: Apa 3 jasa service yang paling sering dilakukan bulan ini?\n"
                   "SQL: SELECT s.name, COUNT(t.id) as frequency FROM services s JOIN transactions t ON s.id = t.service_id WHERE EXTRACT(MONTH FROM t.created_at) = EXTRACT(MONTH FROM CURRENT_DATE) GROUP BY s.name ORDER BY frequency DESC LIMIT 3;\n"),
        ("human", "{question}")
    ])
    
    try:
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", api_key=settings.GEMINI_API_KEY)
        chain = prompt | llm
        result = chain.invoke({"question": last_message})
        generated_sql = result.content.strip().replace("```sql", "").replace("```", "").strip()
        logger.info(f"Generated SQL: {generated_sql}")
        return {"generated_sql": generated_sql}
    except Exception as e:
        logger.error(f"SQL Generation error: {e}")
        return {"generated_sql": None, "error_log": str(e), "status": "error"}
