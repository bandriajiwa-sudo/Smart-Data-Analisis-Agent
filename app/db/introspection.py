import logging
import asyncpg
from cachetools import TTLCache
from app.core.config import settings

logger = logging.getLogger(__name__)

# W10: Performance Optimization Caching (TTL 15 menit)
schema_cache = TTLCache(maxsize=1, ttl=900)

async def fetch_database_schema() -> str:
    """Introspeksi PostgreSQL public tables and columns secara dinamis (Cached)."""
    if "latest_schema" in schema_cache:
        logger.info("Loading schema from memory cache")
        return schema_cache["latest_schema"]
        
    query = """
    SELECT 
        table_name, 
        column_name
    FROM information_schema.columns 
    WHERE table_schema = 'public' 
    ORDER BY table_name, ordinal_position;
    """
    
    try:
        conn = await asyncpg.connect(settings.POS_DB_URI)
        try:
            rows = await conn.fetch(query)
            schema_dict = {}
            for r in rows:
                t_name = r['table_name']
                c_name = r['column_name']
                if t_name not in schema_dict:
                    schema_dict[t_name] = []
                schema_dict[t_name].append(c_name)
                
            output = []
            for table, cols in schema_dict.items():
                col_str = ", ".join(cols)
                output.append(f"Table: {table}\nColumns: {col_str}")
                
            result = "\n".join(output)
            logger.info("Dynamic schema introspection successful. Caching data.")
            schema_cache["latest_schema"] = result
            return result
        finally:
            await conn.close()
    except Exception as e:
        logger.error(f"Gagal melakukan introspeksi skema database POS: {e}")
        return ""
