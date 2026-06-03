"""
One-shot migration: copies all data from dispute_resolution.db (SQLite) → PostgreSQL.
Run once after PostgreSQL is set up:
    python scripts/migrate_sqlite_to_pg.py
"""
import os
import sys
import json
import sqlite3
from pathlib import Path

# ── bootstrap path so we can import project modules ──────────────────────────
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import text
from database.database import engine, init_db, SessionLocal
import database.models  # noqa — registers all models

SQLITE_PATH = ROOT / "dispute_resolution.db"

# Tables in dependency order (parents before children)
TABLES = [
    "bank_customers",
    "dispute_cases",
    "audit_logs",
    "workflow_states",
    "case_notes",
    "document_requests",
]

# Boolean columns per table — SQLite stores as 0/1 int, PostgreSQL needs True/False
BOOL_COLS: dict[str, set] = {
    "dispute_cases": {
        "fraud_selected", "fraud_suspicion", "workflow_ready",
        "sla_breached", "requires_manual_review", "evidence_match", "fallback_mode",
    },
    "audit_logs":        {"success"},
    "workflow_states":   {"success"},
    "case_notes":        {"is_internal"},
    "document_requests": {"fulfilled"},
}


def _cast_row(table: str, record: dict) -> dict:
    """Convert SQLite integer booleans → Python booleans for PostgreSQL."""
    bool_cols = BOOL_COLS.get(table, set())
    for col in bool_cols:
        if col in record and record[col] is not None:
            record[col] = bool(record[col])
    return record


def migrate():
    print(f"Source : {SQLITE_PATH}")
    print(f"Target : {os.environ['DATABASE_URL']}\n")

    if not SQLITE_PATH.exists():
        print("ERROR: dispute_resolution.db not found")
        sys.exit(1)

    # Create all tables in PostgreSQL
    print("Creating tables in PostgreSQL...")
    init_db()
    print("Tables created.\n")

    src = sqlite3.connect(str(SQLITE_PATH))
    src.row_factory = sqlite3.Row

    with engine.connect() as pg:
        for table in TABLES:
            rows = src.execute(f"SELECT * FROM {table}").fetchall()
            if not rows:
                print(f"  {table}: 0 rows — skipped")
                continue

            cols = rows[0].keys()
            col_list = ", ".join(f'"{c}"' for c in cols)
            placeholders = ", ".join(f":{c}" for c in cols)
            insert_sql = text(
                f'INSERT INTO {table} ({col_list}) VALUES ({placeholders}) '
                f'ON CONFLICT DO NOTHING'
            )

            data = [_cast_row(table, dict(row)) for row in rows]

            pg.execute(insert_sql, data)
            pg.commit()
            print(f"  {table}: {len(data)} rows migrated")

    src.close()
    print("\nMigration complete.")


if __name__ == "__main__":
    migrate()
