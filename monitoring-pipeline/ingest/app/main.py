# ingest/app/main.py
import os
import json
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse
from .schemas import IngestPayload
from .db import init_db_pool, close_db_pool
from typing import List, Tuple
# add this import near top of file
from datetime import datetime

INGEST_TOKEN = os.getenv("INGEST_API_TOKEN", "devtoken123")

app = FastAPI(title="Ingest API")

@app.on_event("startup")
async def startup():
    await init_db_pool()

@app.on_event("shutdown")
async def shutdown():
    await close_db_pool()

def check_auth(authorization: str):
    if not authorization:
        return False
    expected = f"Bearer {INGEST_TOKEN}"
    return authorization == expected

def prepare_host_metric_rows(payload: IngestPayload) -> List[Tuple]:
    # ensure payload.time is a datetime object
    ts = payload.time
    if isinstance(ts, str):
        # handle 'Z' timezone (UTC) by converting to +00:00 form
        ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    rows = []
    for m in payload.metrics:
        meta_json = json.dumps(m.meta) if getattr(m, "meta", None) else None
        rows.append((ts, payload.host_id, m.metric, float(m.value), meta_json))
    return rows

def prepare_process_rows(payload: IngestPayload) -> List[Tuple]:
    ts = payload.time
    if isinstance(ts, str):
        ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    rows = []
    if not payload.processes:
        return rows
    for p in payload.processes:
        rows.append((
            ts,
            payload.host_id,
            p.pid,
            p.name,
            p.cpu_pct,
            p.mem_mb,
            p.io_read_bytes,
            p.io_write_bytes,
            p.threads
        ))
    return rows

@app.post("/api/v1/ingest")
async def ingest(payload: IngestPayload, authorization: str = Header(None)):
    if not check_auth(authorization):
        raise HTTPException(status_code=401, detail="unauthorized")

    pool = await init_db_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            host_rows = prepare_host_metric_rows(payload)
            if host_rows:
                await conn.executemany(
                    "INSERT INTO host_metrics(time, host_id, metric_name, metric_value, metric_meta) VALUES($1,$2,$3,$4,$5) ON CONFLICT DO NOTHING",
                    host_rows
                )

            proc_rows = prepare_process_rows(payload)
            if proc_rows:
                await conn.executemany(
                    "INSERT INTO process_metrics(time, host_id, pid, proc_name, cpu_pct, mem_mb, io_read_bytes, io_write_bytes, threads) VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9) ON CONFLICT DO NOTHING",
                    proc_rows
                )

    return JSONResponse({"inserted_host_metrics": len(host_rows), "inserted_process_metrics": len(proc_rows)})
