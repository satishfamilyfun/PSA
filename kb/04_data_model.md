# Data Model

SQLite database at /Library/database/photos.db. Later phases add tables through migrations.

## Phase 1 tables
- **photos**: photo_id, library_path, original_source, source_id, sha256, phash, date_taken, date_suspect, gps_lat, gps_lon, camera, is_screenshot, is_duplicate, duplicate_of, processed_by_api, imported_at
- **sources**: source_id, path, label (for example "Mom's phone backup")
- **faces**: face_id, photo_id, cluster_id, person_id (nullable = Unknown), bounding_box, confidence
- **people**: person_id, name, relationship, created_at (maximum 15 rows enforced by the app)
- **labels**: photo_id, label, score (from the Vision API)
- **detected_text**: photo_id, text (OCR from the Vision API)
- **api_usage**: run_id, photos_sent, estimated_cost, actual_cost, run_at

## Phase 2 tables
- **duplicate_groups**: group_id, photo_id, kept (boolean), removed_at
- **quality_scores**: photo_id, sharpness, exposure, eyes_open, overall
- **events**: event_id, name, type (birthday, anniversary, trip, holiday), date_start, date_end, recurring, person_id
- **search_history**: query_text, filters_json, run_at

## Phase 3 tables
- **profiles**: profile_id, name, is_child
- **photo_visibility**: photo_id, profile_id, visibility (private or shared)

## Rules
- Deleting a person sets faces.person_id to NULL (Unknown); photos are never deleted.
- original_source is written once at import and never changed.
