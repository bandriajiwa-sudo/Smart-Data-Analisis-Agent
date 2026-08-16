import logging
import asyncpg
from decimal import Decimal
from datetime import datetime, date
from app.agent.state import AgentState
from app.core.config import settings

logger = logging.getLogger(__name__)

def json_serializable(row: dict) -> dict:
    """W8: Sanitize database datatypes for LangGraph checkpoint JSON storage"""
    cleaned = {}
    for k, v in row.items():
        if isinstance(v, Decimal):
            cleaned[k] = float(v)
        elif isinstance(v, (datetime, date)):
            cleaned[k] = v.isoformat()
        else:
            cleaned[k] = v
    return cleaned

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
            query_result = [json_serializable(dict(row)) for row in rows]
            logger.info(f"Fetch success, Row count: {len(query_result)}")
            return {"query_result": {"data": query_result[:100]}, "error_log": None, "status": "processing"}
        finally:
            await conn.close()
            
    except Exception as e:
        logger.error(f"SQL Execution error detail: {e}")
        # Jika postgres melemparkan syntax error, lempar log ke loop error_handler
        return {"error_log": str(e), "query_result": None}
