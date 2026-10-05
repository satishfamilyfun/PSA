# Photo Sorting App - code

Built by the developer agents (`/dev-implement <KEY>`). Ownership by folder:

| Folder | Owner agent |
|---|---|
| `core/db/` (migrations, queries) | database-developer |
| `core/metadata/` (EXIF and other extraction logic) | senior-developer |
| `core/utils/` (small helpers) | junior-developer |
| `tests/` (Python unit tests; `test_db_*` also by database-developer) | junior-developer |
| `ui/` (React + TypeScript components, Vitest tests) | ui-developer |

Run Python tests: `pytest app` · Run UI tests: `cd app/ui; npm test`
