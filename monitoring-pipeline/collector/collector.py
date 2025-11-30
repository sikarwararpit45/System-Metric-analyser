# collector/collector.py
import os
import time
import json
import requests
from datetime import datetime, timezone
import psutil
import argparse

# Config from environment or defaults
INGEST_HOST = os.getenv("INGEST_HOST", "localhost")
INGEST_PORT = os.getenv("INGEST_PORT", "8000")
INGEST_API_TOKEN = os.getenv("INGEST_API_TOKEN", "devtoken123")
INTERVAL = int(os.getenv("COLLECTOR_INTERVAL_SECONDS", "1"))

INGEST_URL = f"http://{INGEST_HOST}:{INGEST_PORT}/api/v1/ingest"
HEADERS = {"Authorization": f"Bearer {INGEST_API_TOKEN}", "Content-Type": "application/json"}

def sample_once(host_id="local-dev"):
    now = datetime.now(timezone.utc).isoformat()
    cpu_total = psutil.cpu_percent(interval=None)
    mem = psutil.virtual_memory()
    mem_used_mb = round(mem.used / (1024 * 1024), 2)
    # top processes by CPU (limit to top 5)
    procs = []
    # first call to cpu_percent per process may return 0.0, so call once to populate
    for p in psutil.process_iter(attrs=['pid', 'name']):
        try:
            p.cpu_percent(interval=None)
        except Exception:
            continue
    time.sleep(0.1)  # small pause to let psutil gather cpu_percent deltas

    for p in psutil.process_iter(attrs=['pid', 'name', 'cpu_percent', 'memory_info']):
        try:
            cpu = p.info.get('cpu_percent') or 0.0
            mem_mb = (p.info.get('memory_info').rss / (1024 * 1024)) if p.info.get('memory_info') else 0
            procs.append((cpu, p.info['pid'], p.info.get('name'), round(mem_mb, 2)))
        except Exception:
            continue
    procs_sorted = sorted(procs, key=lambda x: x[0], reverse=True)[:5]
    processes_payload = []
    for cpu, pid, name, mem_mb in procs_sorted:
        processes_payload.append({
            "pid": pid,
            "name": name,
            "cpu_pct": cpu,
            "mem_mb": mem_mb
        })

    payload = {
        "host_id": host_id,
        "time": now,
        "metrics": [
            {"metric": "cpu_total_pct", "value": cpu_total},
            {"metric": "mem_used_mb", "value": mem_used_mb}
        ],
        "processes": processes_payload,
        "tags": {"env": "dev"}
    }
    return payload

def send(payload):
    try:
        r = requests.post(INGEST_URL, headers=HEADERS, json=payload, timeout=5)
        r.raise_for_status()
        return r.status_code, r.json()
    except Exception as e:
        return None, str(e)

def loop_send(host_id="local-dev", interval=1):
    print(f"collector: sending to {INGEST_URL} every {interval}s")
    while True:
        p = sample_once(host_id=host_id)
        status, resp = send(p)
        print("sent ->", status, resp)
        time.sleep(interval)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dev-send-loop", action="store_true", help="continuously sample and send")
    parser.add_argument("--host-id", type=str, default="local-dev")
    parser.add_argument("--interval", type=int, default=INTERVAL)
    args = parser.parse_args()

    if args.dev_send_loop:
        loop_send(host_id=args.host_id, interval=args.interval)
    else:
        p = sample_once(host_id=args.host_id)
        status, resp = send(p)
        print("result:", status, resp)
