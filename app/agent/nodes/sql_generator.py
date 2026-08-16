import logging
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from app.agent.state import AgentState
from app.core.config import settings

logger = logging.getLogger(__name__)

SCHEMA_CONTEXT = """
Table: sales
Columns: id, invoice_number, total, tax, discount, grand_total, payment_method, created_at, outlet_id
Table: sale_items
Columns: id, sale_id, product_id, quantity, unit_price, subtotal
Table: products
Columns: id, name, category_id, price, stock
"""

def node_sql_generator(state: AgentState) -> dict:
    """Menghasilkan raw SQL query berdasarkan intent"""
    if state.intent == "general_chat":
        return {}

    messages = state.messages
    last_message = messages[-1].content if hasattr(messages[-1], "content") else str(messages[-1])
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Anda adalah PostgreSQL Data Analyst AI. Buat satu baris query postgres untuk menjawab input user. \n"
                   "DILARANG menulis markdown atau penjelasan apapun. HANYA OUTPUTKAN PURE SQL.\n"
                   f"Skema Database:\n{SCHEMA_CONTEXT}\n"
                   "Fungsi tanggal standar: gunakan CURRENT_DATE."),
        ("human", "{question}")
    ])
    
    try:
        llm = ChatOpenAI(model="gpt-4o-mini", api_key=settings.OPENAI_API_KEY)
        chain = prompt | llm
        result = chain.invoke({"question": last_message})
        generated_sql = result.content.strip().replace("```sql", "").replace("```", "").strip()
        logger.info(f"Generated SQL: {generated_sql}")
        return {"generated_sql": generated_sql}
    except Exception as e:
        logger.error(f"SQL Generation error: {e}")
        return {"generated_sql": None, "error_log": str(e), "status": "error"}
