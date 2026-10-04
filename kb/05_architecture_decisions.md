# Architecture Decision Records

Format: a short version of MADR (context, decision, consequences).

| ADR | Decision | Context and reason | Consequences |
|-----|----------|--------------------|--------------|
| ADR-001 | Windows desktop app (Tauri + React UI, Python core) | Family uses Windows; photos stay local; Python has the best image and ML libraries | Mac and Linux need extra builds later |
| ADR-002 | Copy, never move | Originals are the safety net | Needs roughly 50 GB of extra disk space for 10,000 photos |
| ADR-003 | One-time cloud Vision API pass | About $15 for 10,000 photos, far cheaper than hosting models | Each new photo costs about $0.0015; results must be stored carefully |
| ADR-004 | SQLite in the library folder | Zero setup, portable, enough for this scale | Not designed for concurrent multi-device use (revisit in Phase 3) |
| ADR-005 | Local face clustering | Free and private after the API pass | Clustering quality depends on threshold tuning |
| ADR-006 | Only 10-15 tracked people | Keeps labeling to about 30 minutes; other faces are Unknown | Searches ignore untracked people |
| ADR-007 | Never permanently delete | Family photos are irreplaceable | Phase 2 removals go to the Recycle Bin |
| ADR-008 | Natural language search translates to filters | Keeps search predictable and testable; only text goes to the LLM | Phase 2 dependency on an LLM API |
