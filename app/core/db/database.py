"""SQLite access and migrations for the Photo Sorting App.

Migrations are numbered .sql files in ./migrations, applied once each in order.
Add a new file (002_..., 003_...) to change the schema; never edit an applied migration.
"""
import sqlite3
from pathlib import Path

MIGRATIONS_DIR = Path(__file__).parent / "migrations"


def connect(db_path: str | Path = ":memory:") -> sqlite3.Connection:
    """Open the database with foreign keys on and rows accessible by column name."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def applied_migrations(conn: sqlite3.Connection) -> set[str]:
    conn.execute("CREATE TABLE IF NOT EXISTS schema_migrations (name TEXT PRIMARY KEY, "
                 "applied_at TEXT NOT NULL DEFAULT (datetime('now')))")
    return {row["name"] for row in conn.execute("SELECT name FROM schema_migrations")}


def migrate(conn: sqlite3.Connection) -> list[str]:
    """Apply pending migrations in order. Returns the names applied in this call."""
    done = applied_migrations(conn)
    applied = []
    for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
        if path.name in done:
            continue
        with conn:
            conn.executescript(path.read_text(encoding="utf-8"))
            conn.execute("INSERT INTO schema_migrations (name) VALUES (?)", (path.name,))
        applied.append(path.name)
    return applied


def columns(conn: sqlite3.Connection, table: str) -> set[str]:
    return {row["name"] for row in conn.execute(f"PRAGMA table_info({table})")}
