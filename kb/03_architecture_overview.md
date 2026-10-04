# Architecture Overview

Structure follows a light version of arc42 with C4 diagrams.

## System context (C4 level 1)
```
 [Family members] --use--> [Photo Sorting App (Windows desktop)]
                                 |            |             |
                     reads copies of   one-time call   (Phase 2) query text only
                                 v            v             v
                    [Source folders]  [Cloud Vision API]  [LLM API]
                    external drive,
                    phone backups
```

## Containers (C4 level 2)
```
 +---------------------- Photo Sorting App -----------------------+
 |                                                                |
 |  [Desktop UI]  React + Tauri                                   |
 |       | local HTTP / IPC                                       |
 |  [Core service]  Python FastAPI                                |
 |       |-- Import pipeline      (copy, EXIF, screenshot, dupes) |
 |       |-- Enrichment worker    (Vision API, face clustering)   |
 |       |-- Search service       (filters; Phase 2 NL search)    |
 |       |-- People service       (labels, merge, Unknown)        |
 |       |                                                        |
 |  [SQLite: photos.db]   [Library folder: photos/, cache/]       |
 +----------------------------------------------------------------+
```

## Key components (C4 level 3, core service)
| Component | Responsibility | Phase |
|-----------|----------------|-------|
| SourceScanner | Walks source folders, lists image files | 1 |
| Copier | Copies to YYYY/MM, records original path, resumable | 1 |
| ExifReader | Date, GPS, camera; HEIC via pillow-heif | 1 |
| ScreenshotDetector | Heuristics: screen size, no camera EXIF, file name patterns | 1 |
| DuplicateDetector | SHA-256 for exact, perceptual hash for near-duplicates | 1 |
| VisionClient | One call per photo, retry, cost tracking | 1 |
| FaceClusterer | Local clustering of face embeddings | 1 |
| SearchEngine | SQL filters by person, date, location | 1 |
| DuplicateReviewer | Side-by-side review, Recycle Bin removal | 2 |
| QualityScorer | Sharpness, exposure, eyes open | 2 |
| NLQueryTranslator | Text to filter JSON via LLM | 2 |
| EventStore | Birthdays, anniversaries, trips | 2 |
| ProfileManager | Profiles, private and shared photos | 3 |

## Runtime view: import
1. User picks sources and options in the import wizard.
2. SourceScanner lists files; Copier copies them and ExifReader extracts metadata.
3. ScreenshotDetector and DuplicateDetector mark records; nothing is deleted.
4. The summary screen shows counts. Enrichment runs as a separate, resumable job.

## Deployment
Single Windows install: Tauri shell bundling the UI and a packaged Python service. Library folder chosen by the user (default C:\Users\<name>\PhotoLibrary).
