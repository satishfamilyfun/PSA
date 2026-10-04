# Requirements

## Functional requirements by epic

### E1 Import and organize (Phase 1)
- FR-1.1 Import from multiple source folders in one run (external drive, phone backup folders).
- FR-1.2 Copy each photo to /Library/photos/YYYY/MM/, or /Library/photos/undated/ without a date.
- FR-1.3 Never move, rename or modify originals; store each photo's original source path.
- FR-1.4 Detect screenshots; the user chooses whether to skip them.
- FR-1.5 Detect exact and near-duplicates and flag them. No deletion in Phase 1.
- FR-1.6 Show an import summary: imported, skipped screenshots, flagged duplicates, errors.

### E2 Metadata (Phase 1)
- FR-2.1 Extract date taken and GPS from EXIF, including HEIC files.
- FR-2.2 Flag suspicious dates (before 1990, in the future, scanner defaults).
- FR-2.3 Send each photo to the Vision API once; store labels, text and face boxes locally.
- FR-2.4 Show estimated cost before a Vision API batch and actual cost after.

### E3 People (Phase 1)
- FR-3.1 Cluster faces locally.
- FR-3.2 Let users name clusters; at most 15 tracked people.
- FR-3.3 Faces not assigned to a tracked person are "Unknown" and excluded from people searches.
- FR-3.4 Add, rename, merge and remove people without deleting photos.

### E4 Search and browse (Phase 1)
- FR-4.1 Filter by person (one or more), date range and location; combine filters.
- FR-4.2 Thumbnail gallery and detail view.

### E5 Duplicate cleanup and quality (Phase 2)
- FR-5.1 Review duplicate groups side by side; removed copies go to the Recycle Bin.
- FR-5.2 Suggest the best shot in a group of similar photos.

### E6 Smart search and life events (Phase 2)
- FR-6.1 Natural language search translated into the same filters as FR-4.1.
- FR-6.2 Record birthdays, anniversaries and trips; use them in search.

### E7 Sharing and multi-user (Phase 3)
- FR-7.1 Export albums to a folder or zip.
- FR-7.2 Family profiles with private and shared photos.
- FR-7.3 Signed Windows installer with auto-update.

### E8 Memories and collages
- FR-8.1 Birthday collage helper (Phase 1).
- FR-8.2 Collage layout builder with print export (Phase 2).

## Non-functional requirements
| ID | Category | Requirement |
|----|----------|-------------|
| NFR-1 | Performance | Import and EXIF extraction of 10,000 photos completes in under 60 minutes on a typical laptop. |
| NFR-2 | Performance | Filter searches return in under 2 seconds for 10,000 photos. |
| NFR-3 | Cost | Vision API processing costs about $1.50 per 1,000 photos, one time only. Searches cost nothing (Phase 1). |
| NFR-4 | Privacy | Photos and face data stay on the local machine after the one-time API pass. |
| NFR-5 | Safety | The app never permanently deletes files; removals go to the Recycle Bin (Phase 2). |
| NFR-6 | Usability | A 10-year-old can import and search without help. Plain words, large buttons. |
| NFR-7 | Reliability | An interrupted import can resume without duplicating work. |
| NFR-8 | Platform | Windows 10 and 11. |
| NFR-9 | Offline | Everything except the API pass and natural language search works offline. |
