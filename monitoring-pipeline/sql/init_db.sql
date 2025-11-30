-- init_db.sql
-- Run on DB to create schema and hypertables

-- Enable Timescale extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Hosts metadata
CREATE TABLE IF NOT EXISTS hosts (
  host_id TEXT PRIMARY KEY,
  hostname TEXT,
  os TEXT,
  agent_version TEXT,
  tags JSONB
);

-- Host-level metrics
CREATE TABLE IF NOT EXISTS host_metrics (
  time TIMESTAMPTZ NOT NULL,
  host_id TEXT NOT NULL,
  metric_name TEXT NOT NULL,
  metric_value DOUBLE PRECISION,
  metric_meta JSONB,
  PRIMARY KEY (time, host_id, metric_name)
);

SELECT create_hypertable('host_metrics', 'time', if_not_exists => TRUE, chunk_time_interval => INTERVAL '1 day');

-- Process metrics (top-N approach)
CREATE TABLE IF NOT EXISTS process_metrics (
  time TIMESTAMPTZ NOT NULL,
  host_id TEXT NOT NULL,
  pid INT NOT NULL,
  proc_name TEXT,
  cpu_pct DOUBLE PRECISION,
  mem_mb DOUBLE PRECISION,
  io_read_bytes BIGINT,
  io_write_bytes BIGINT,
  threads INT,
  PRIMARY KEY (time, host_id, pid)
);

SELECT create_hypertable('process_metrics', 'time', if_not_exists => TRUE, chunk_time_interval => INTERVAL '1 day');

-- Disk health SMART (example)
CREATE TABLE IF NOT EXISTS disk_health (
  time TIMESTAMPTZ NOT NULL,
  host_id TEXT NOT NULL,
  device TEXT,
  attribute TEXT,
  value DOUBLE PRECISION,
  raw JSONB,
  PRIMARY KEY (time, host_id, device, attribute)
);

SELECT create_hypertable('disk_health', 'time', if_not_exists => TRUE);

-- Continuous aggregate: CPU 1-minute average
CREATE MATERIALIZED VIEW IF NOT EXISTS cpu_1min
WITH (timescaledb.continuous) AS
SELECT time_bucket('1 minute', time) AS bucket,
       host_id,
       avg(metric_value) AS cpu_avg
FROM host_metrics
WHERE metric_name = 'cpu_total_pct'
GROUP BY bucket, host_id;
