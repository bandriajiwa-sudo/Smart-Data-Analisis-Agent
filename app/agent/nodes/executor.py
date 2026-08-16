import logging
import asyncpg
from app.agent.state import AgentState
from app.core.config import settings

logger = logging.getLogger(__name__)

async def node_sql_executor(state: AgentState) -> dict:
    """Mengeksekusi SQL secara asinkron menggunakan koneksi read-only DB-POS."""
    generated_sql = state.generated_sql
    if not generated_sql:
        return {"status": "error", "error_log": "SQL Query tidak ditemukan/kosong."}
        
    try:
        # Menghalau DML injection statis 
        if not generated_sql.strip().upper().startswith("SELECT"):
            raise ValueError("Security block: Hanya command SELECT yang diizinkan!")
            
        conn = await asyncpg.connect(settings.POS_DB_URI)
        try:
            rows = await conn.fetch(generated_sql)
            query_result = [dict(row) for row in rows]
            logger.info(f"Fetch success, Row count: {len(query_result)}")
            return {"query_result": {"data": query_result[:100]}, "error_log": None, "status": "processing"}
        finally:
            await conn.close()
            
    except Exception as e:
        logger.error(f"SQL Execution error detail: {e}")
        # Jika postgres melemparkan syntax error, lempar log ke loop error_handler
        return {"error_log": str(e), "query_result": None}
