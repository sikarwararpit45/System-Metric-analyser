# ingest/app/db.py
import os
from typing import Optional
import asyncpg

_db_pool: Optional[asyncpg.pool.Pool] = None

def get_dsn():
    user = os.getenv("POSTGRES_USER", "tsdb")
    pwd = os.getenv("POSTGRES_PASSWORD", "tsdbpass")
    host = os.getenv("POSTGRES_HOST", "timescaledb")
    port = int(os.getenv("POSTGRES_PORT", 5432))
    db = os.getenv("POSTGRES_DB", "metrics")
    return f"postgresql://{user}:{pwd}@{host}:{port}/{db}"

async def init_db_pool():
    global _db_pool
    if _db_pool is None:
        _db_pool = await asyncpg.create_pool(dsn=get_dsn(), min_size=1, max_size=10)
    return _db_pool

async def close_db_pool():
    global _db_pool
    if _db_pool is not None:
        await _db_pool.close()
        _db_pool = None

