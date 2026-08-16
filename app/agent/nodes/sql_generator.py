import logging
from langchain_groq import ChatGroq
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
        ("system", "Anda adalah PostgreSQL Data Analyst AI. Buat satu baris query postgres untuk menjawab input user. \n"
                   "DILARANG menulis markdown atau penjelasan apapun. HANYA OUTPUTKAN PURE SQL.\n"
                   f"Skema Database:\n{SCHEMA_CONTEXT}\n"
                   "Fungsi tanggal standar: gunakan CURRENT_DATE.\n\n"
                   "--- CONTOH QUERY / FEW-SHOT EXAMPLES ---\n"
                   "User: Berapa total penjualan hari ini?\n"
                   "SQL: SELECT COALESCE(SUM(total), 0) FROM sales WHERE DATE(created_at) = CURRENT_DATE;\n\n"
                   "User: Apa 3 produk terjual paling banyak?\n"
                   "SQL: SELECT p.name, SUM(si.quantity) as qty FROM sale_items si JOIN products p ON si.product_id = p.id GROUP BY p.name ORDER BY qty DESC LIMIT 3;\n"),
        ("human", "{question}")
    ])
    
    try:
        llm = ChatGroq(model="llama-3.3-70b-versatile", api_key=settings.GROQ_API_KEY)
        chain = prompt | llm
        result = chain.invoke({"question": last_message})
        generated_sql = result.content.strip().replace("```sql", "").replace("```", "").strip()
        logger.info(f"Generated SQL: {generated_sql}")
        return {"generated_sql": generated_sql}
    except Exception as e:
        logger.error(f"SQL Generation error: {e}")
        return {"generated_sql": None, "error_log": str(e), "status": "error"}
