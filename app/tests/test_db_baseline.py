from app.core.db.database import columns, connect, migrate


def test_migrations_apply_once():
    conn = connect()
    assert "001_initial.sql" in migrate(conn)
    assert migrate(conn) == []


def test_baseline_photos_table():
    conn = connect()
    migrate(conn)
    assert {"photo_id", "library_path", "original_source", "sha256"} <= columns(conn, "photos")
