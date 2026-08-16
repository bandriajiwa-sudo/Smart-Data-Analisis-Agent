import logging
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from app.agent.state import AgentState
from app.core.config import settings

logger = logging.getLogger(__name__)

ERROR_CORRECTION_PROMPT = """Anda adalah SQL Debugger Expert. Database yang digunakan adalah PostgreSQL.

Query SQL yang gagal:
{generated_sql}

Pesan error dari PostgreSQL:
{error_log}

Daftar tabel yang tersedia: sales, sale_items, products
Daftar kolom valid:
- sales: id, invoice_number, total, tax, discount, grand_total, payment_method, created_at, outlet_id
- sale_items: id, sale_id, product_id, quantity, unit_price, subtotal
- products: id, name, category_id, price, stock

STRATEGI KOREKSI (Wajib Diterapkan):
1. Error "column/relation does not exist" -> Periksa typo. (Contoh 'sale' -> 'sales', 'totl' -> 'total').
2. Error "function does not exist" -> Gunakan fungsi Postgres valid (Contoh TODAY() -> CURRENT_DATE).
3. Error sintaks/aggregasi -> Ganti dengan GROUP BY yang sesuai.
4. Kembalikan HANYA MURNI SQL tanpa teks penjelasan sama sekali."""

def node_error_handler(state: AgentState) -> dict:
    """Implementasi fail-over / Self Healing LangGraph loop"""
    error_log = state.error_log
    old_sql = state.generated_sql
    retry_count = state.retry_count + 1
    
    if retry_count > 3:
        logger.warning(f"Max retry limit exception. Stopped at: {error_log}")
        return {"status": "error", "retry_count": retry_count, "error_log": f"Max retry (3) reached: {error_log}"}
        
    prompt = ChatPromptTemplate.from_template(ERROR_CORRECTION_PROMPT)
    llm = ChatGroq(model="llama-3.1-70b-versatile", api_key=settings.GROQ_API_KEY)
    
    try:
        chain = prompt | llm
        result = chain.invoke({"generated_sql": old_sql, "error_log": error_log})
        corrected_sql = result.content.strip().replace("```sql", "").replace("```", "").strip()
        logger.info(f"Langgraph Self-healed SQL Retry {retry_count} -> {corrected_sql}")
        return {"generated_sql": corrected_sql, "retry_count": retry_count, "error_log": None, "status": "processing"}
    except Exception as e:
        logger.error(f"Failed inside self healing fallback: {e}")
        return {"status": "error", "retry_count": retry_count, "error_log": str(e)}
