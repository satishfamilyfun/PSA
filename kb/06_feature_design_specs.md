# Feature Design Specs

One short spec per epic. Stories in Jira hold the detailed acceptance criteria.

## E1 Import and organize
Wizard with four steps: choose sources, options, progress, summary. Options: organize by date or keep structure, skip screenshots, flag duplicates, skip images under 100 KB. Wireframe v0.2 is attached to the import wizard story.

## E2 Metadata
EXIF is read at import. Suspicious dates are flagged, not corrected. The Vision API job runs after import with a cost estimate first, and can be paused and resumed.

## E3 People
Labeling screen shows one cluster at a time with sample faces, a name field, and the list of tracked people (maximum 15). Actions: save name, mark Unknown, skip. The number of sample faces per cluster is an open decision on the clustering story. Mockup v0.1 is attached to the labeling story.

## E4 Search and browse
Filter bar: people (multi-select), date range, location (place name or map area). Results in a thumbnail grid; detail view shows date, place and people.

## E5 Duplicate cleanup and quality (Phase 2)
Side-by-side comparison of a duplicate group with a suggested best shot. Remove sends files to the Recycle Bin. Originals on source drives are never touched.

## E6 Smart search and life events (Phase 2)
A search box accepts plain language. The translator returns filter JSON, which is shown to the user as editable filter chips. Events are managed on a simple dates screen.

## E7 Sharing and multi-user (Phase 3)
Export albums; family profiles with a child mode; signed installer with auto-update.

## E8 Memories and collages
Phase 1 helper gathers candidates (June 9 birthday photos, family photos by year, solo portraits). Phase 2 builder arranges photos into templates and exports for print.
