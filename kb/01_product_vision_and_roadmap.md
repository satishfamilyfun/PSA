# Product Vision and Roadmap

## Problem
Our family has about 10,000 photos spread across an external hard drive and several phones. Finding specific photos (birthdays, family photos over the years, trips) takes a long time, and duplicates and screenshots are mixed in with real photos.

## Vision
A Windows desktop app that brings all family photos into one organized library, recognizes the people we care about, and lets anyone in the family, including the kids, find photos by person, date, place or a plain-language question. Later, friends can install it for their own families.

## Guiding principles
- Originals are never changed. The app works on copies.
- Photos stay on our own computer. Only the one-time Vision API pass and natural language queries use the cloud.
- Simple enough for a 10-year-old.
- Nothing is permanently deleted by the app.

## Roadmap
All features below are part of the product. They are sequenced into phases; none are cancelled.

| Phase | Theme | Epics | Key outcome |
|-------|-------|-------|-------------|
| Phase 1 | Library MVP | E1 Import and organize, E2 Metadata, E3 People, E4 Search and browse, E8 Birthday collage helper | One organized library; find photos by person, date and place |
| Phase 2 | Smart library | E5 Duplicate cleanup and quality, E6 Smart search and life events, E8 Collage builder | Clean library, natural language search, event-aware search |
| Phase 3 | Share and scale | E7 Sharing and multi-user | Family profiles, sharing, installer for friends |

## Phase boundaries that matter for stories
- Duplicates: Phase 1 only detects and flags them ({{S9}}). Reviewing and removing them is Phase 2 ({{S14}}).
- Search: Phase 1 is filter-based ({{S7}}). Natural language search is Phase 2 ({{S16}}).
- Dates and events: Phase 1 uses EXIF dates only. Named events such as birthdays are Phase 2 ({{S17}}).
- Users: Phase 1 has one shared family library with no logins. Profiles are Phase 3 ({{S19}}).
