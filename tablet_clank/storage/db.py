import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS schema_migrations (version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS sources (id TEXT PRIMARY KEY, manufacturer TEXT NOT NULL, region TEXT NOT NULL, kind TEXT NOT NULL, url TEXT NOT NULL, state TEXT NOT NULL, enabled INTEGER NOT NULL DEFAULT 1);
CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY, manufacturer TEXT NOT NULL, family TEXT, name TEXT NOT NULL, model_number TEXT, sku TEXT, region TEXT NOT NULL, variant TEXT, connectivity TEXT, ram_gb REAL, storage_gb INTEGER, colour TEXT, processor TEXT, display_size_in REAL, os TEXT, identity_key TEXT NOT NULL UNIQUE, first_seen TEXT NOT NULL, last_seen TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS observations (id INTEGER PRIMARY KEY, product_id INTEGER NOT NULL REFERENCES products(id), source_id TEXT NOT NULL REFERENCES sources(id), url TEXT NOT NULL, observed_at TEXT NOT NULL, raw_values TEXT NOT NULL, normalized_values TEXT NOT NULL, collector TEXT NOT NULL, UNIQUE(product_id, source_id, observed_at));
CREATE TABLE IF NOT EXISTS collector_runs (id INTEGER PRIMARY KEY, source_id TEXT NOT NULL REFERENCES sources(id), started_at TEXT NOT NULL, finished_at TEXT, status TEXT NOT NULL, raw_count INTEGER NOT NULL DEFAULT 0, validated_count INTEGER NOT NULL DEFAULT 0, rejected_count INTEGER NOT NULL DEFAULT 0, accepted_count INTEGER NOT NULL DEFAULT 0, new_count INTEGER NOT NULL DEFAULT 0, updated_count INTEGER NOT NULL DEFAULT 0, resighted_count INTEGER NOT NULL DEFAULT 0, error TEXT);
CREATE TABLE IF NOT EXISTS rejected_candidates (id INTEGER PRIMARY KEY, run_id INTEGER NOT NULL REFERENCES collector_runs(id), url TEXT NOT NULL, title TEXT NOT NULL, reason TEXT NOT NULL, raw_values TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS change_events (id INTEGER PRIMARY KEY, product_id INTEGER NOT NULL REFERENCES products(id), source_id TEXT NOT NULL REFERENCES sources(id), event_type TEXT NOT NULL, old_value TEXT, new_value TEXT, evidence_url TEXT NOT NULL, observed_at TEXT NOT NULL, confidence REAL NOT NULL);
CREATE TABLE IF NOT EXISTS source_state (source_id TEXT PRIMARY KEY REFERENCES sources(id), baseline_complete INTEGER NOT NULL DEFAULT 0, last_healthy_run_id INTEGER, consecutive_healthy_runs INTEGER NOT NULL DEFAULT 0);
CREATE INDEX IF NOT EXISTS idx_products_manufacturer ON products(manufacturer);
CREATE INDEX IF NOT EXISTS idx_observations_source ON observations(source_id);
"""

class Database:
    def __init__(self, path="var/tablet_clank.db"):
        self.path = Path(path); self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path); self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys=ON"); self.conn.execute("PRAGMA journal_mode=WAL"); self.migrate()
    def migrate(self):
        self.conn.executescript(SCHEMA)
        if not self.conn.execute("SELECT 1 FROM schema_migrations WHERE version=1").fetchone():
            self.conn.execute("INSERT INTO schema_migrations VALUES (1, datetime('now'))")
        self.conn.commit()
    def integrity(self): return self.conn.execute("PRAGMA integrity_check").fetchone()[0]
    def close(self): self.conn.close()
