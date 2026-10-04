-- 001: Phase 1 baseline (PSA story: project skeleton and SQLite schema)
CREATE TABLE IF NOT EXISTS sources (
    source_id INTEGER PRIMARY KEY AUTOINCREMENT,
    path      TEXT NOT NULL UNIQUE,
    label     TEXT
);

CREATE TABLE IF NOT EXISTS photos (
    photo_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    library_path    TEXT NOT NULL UNIQUE,
    original_source TEXT NOT NULL,
    source_id       INTEGER REFERENCES sources(source_id),
    sha256          TEXT,
    imported_at     TEXT NOT NULL DEFAULT (datetime('now'))
);
