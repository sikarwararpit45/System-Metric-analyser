# ingest/app/schemas.py
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class Metric(BaseModel):
    metric: str
    value: float
    meta: Optional[dict] = None

class ProcessMetric(BaseModel):
    pid: int
    name: Optional[str] = None
    cpu_pct: Optional[float] = None
    mem_mb: Optional[float] = None
    io_read_bytes: Optional[int] = None
    io_write_bytes: Optional[int] = None
    threads: Optional[int] = None

class IngestPayload(BaseModel):
    host_id: str
    time: datetime # ISO timestamp
    metrics: List[Metric]
    processes: Optional[List[ProcessMetric]] = None
    tags: Optional[dict] = None
