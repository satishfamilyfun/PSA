---
name: write-db-migration
description: Write SQLite schema changes for the PSA app as new numbered migration files, plus query functions and tests. Use for any database task.
---

# Write a database migration

1. Find the highest migration number in `app/core/db/migrations/` and add the next one,
   for example `002_exif_metadata.sql`. Never edit an existing migration.
2. Use `ALTER TABLE ... ADD COLUMN` for new columns; SQLite cannot drop or rename easily, so plan additively.
3. Types: dates as TEXT in ISO 8601 (`YYYY-MM-DDTHH:MM:SS`), coordinates as REAL (decimal degrees),
   flags as INTEGER 0/1 with `NOT NULL DEFAULT 0`.
4. Match names to the Data Model page (for example `date_taken`, `date_suspect`, `gps_lat`, `gps_lon`, `camera`).
5. Add an index only when a Phase 1 search filters on the column (date and location searches do).
6. If the task includes data access, add small functions to a module in `app/core/db/` with type hints,
   using parameterised queries (`?` placeholders), never string formatting.

## Tests (app/tests/test_db_<topic>.py)
- Migration applies on a fresh in-memory database via `migrate(connect())`.
- New columns exist (use `columns(conn, "photos")`).
- Defaults behave as expected; NULLs allowed where the data may be missing (no GPS, no date).
- Query functions return expected rows.
