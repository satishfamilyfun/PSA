"""Full-product backlog for the Photo Sorting App (PSA) demo project.

All features are kept; they are sequenced into phases, not descoped.

Planted issues the agents should catch:
  Scenario 1 - BA agent on S3 (import wizard):
    - Description says "remove duplicates"; Phase 1 only flags duplicates (KB roadmap, S9),
      deletion is Phase 2 (S14).
    - Attached wireframe shows "Skip screenshots" / "Skip images < 100 KB"; description is silent.
    - No acceptance criteria, vague "organize" wording, no persona.
    - Blocked by S1 (schema); related to S2, S9, S11, S14.
  Scenario 2 - BA agent on S6 (face labeling UI):
    - Blocked by S5 (still To Do) with an unresolved question: 5 or 10 sample faces?
    - Attached mockup shows 6 sample faces -> a third conflicting number.
    - KB: only 10-15 tracked people, others "Unknown"; description is silent.
    - Kids use it (comment + personas page).
  Scenario 3 - QA agent on S4 (EXIF extraction):
    - Story is ready-for-dev with acceptance criteria; attachment holds sample EXIF output
      including a photo without GPS, a scanned photo with a wrong date and a HEIC file.
"""

EPICS = [
    {"id": "E1", "summary": "Import and organize photos",
     "description": "Bring photos from all family sources into one master library organized by date. Originals are never changed. Phase 1."},
    {"id": "E2", "summary": "Metadata extraction",
     "description": "Extract EXIF data locally and run a one-time cloud Vision API pass per photo; store everything locally. Phase 1."},
    {"id": "E3", "summary": "People recognition",
     "description": "Cluster faces and let the family name the 10-15 people they care about. Phase 1."},
    {"id": "E4", "summary": "Search and browse",
     "description": "Find photos by person, date and location, and browse them in a gallery. Phase 1."},
    {"id": "E5", "summary": "Duplicate cleanup and photo quality",
     "description": "Review flagged duplicates, remove them safely, and pick the best shot from similar photos. Phase 2."},
    {"id": "E6", "summary": "Smart search and life events",
     "description": "Natural language search and family events (birthdays, anniversaries, trips) as search context. Phase 2."},
    {"id": "E7", "summary": "Sharing and multi-user",
     "description": "Export and share albums, family profiles, and an installer so friends can use the app. Phase 3."},
    {"id": "E8", "summary": "Memories and collages",
     "description": "Help the family turn photos into collages and memory books, starting with the 10th birthday collage. Phase 1-2."},
]

STORIES = [
    # ---------------- E1 Import and organize (Phase 1) ----------------
    {"id": "S1", "epic": "E1", "summary": "Set up project skeleton and SQLite schema",
     "labels": ["phase-1", "backend"],
     "description": """As the developer, I want the app skeleton and database in place, so that features can be built on a stable base.

## Acceptance criteria
- Given a fresh install, when the app starts, then it creates photos.db in the library folder.
- Given the database, then the tables in the Data Model page (Phase 1 section) exist.""",
     "comments": ["Tech lead: schema is on the Data Model page; Phase 2 and 3 tables are added by later migrations."]},
    {"id": "S2", "epic": "E1", "summary": "Copy photos into master library organized by date",
     "labels": ["phase-1", "backend", "import"],
     "description": """As a family member, I want my photos copied into one library organized by year and month, so that I can find them easily without risking the originals.

## Acceptance criteria
- Given a photo with an EXIF date, when it is imported, then a copy is stored under /Library/photos/YYYY/MM/.
- Given a photo without an EXIF date, then it is stored under /Library/photos/undated/.
- Given any import, then the original file is never moved, renamed or modified.
- Given an imported photo, then its original source path is saved in the database."""},
    {"id": "S3", "epic": "E1", "summary": "Import wizard: import photos from drive and phone backups",
     "labels": ["phase-1", "ui", "import"],
     "description": """As a family member I want to import photos from our external drive and our phone backups so everything is in one place.

The import should remove duplicates and organize the photos. Wireframe attached.""",
     "comments": [
         "Product owner: my wife's phone backup is full of WhatsApp forwards and screenshots. Not sure we want those in the library.",
         "Product owner: the kids should be able to run an import too, so keep it simple.",
     ],
     "attachments": ["assets/import_wizard_wireframe.png"]},
    {"id": "S11", "epic": "E1", "summary": "Detect screenshots during import",
     "labels": ["phase-1", "backend", "import"],
     "description": """As a family member, I want screenshots recognized during import, so that I can keep them out of the family library.

## Acceptance criteria
- Given an image with screen dimensions and no camera EXIF, then it is marked is_screenshot.
- Given the user chose to skip screenshots, then marked images are not copied but are listed in the import summary."""},
    {"id": "S9", "epic": "E1", "summary": "Flag duplicate photos during import",
     "labels": ["phase-1", "backend", "duplicates"],
     "description": """As a family member, I want duplicates flagged during import, so that I can review them later.

## Acceptance criteria
- Given two files with the same hash, then the second is flagged is_duplicate with duplicate_of set.
- Given visually near-identical photos, then they are flagged as near-duplicates.
- Nothing is deleted in Phase 1. Removal is covered by the Phase 2 duplicate review story."""},

    # ---------------- E2 Metadata (Phase 1) ----------------
    {"id": "S4", "epic": "E2", "summary": "Extract EXIF metadata (date taken, GPS)",
     "labels": ["phase-1", "backend", "metadata", "ready-for-dev"],
     "description": """As a family member, I want the date and location of each photo extracted, so that I can search by when and where photos were taken.

## Acceptance criteria
- Given a photo with EXIF DateTimeOriginal, when it is imported, then date_taken is stored.
- Given a photo with GPS tags, then gps_lat and gps_lon are stored as decimal degrees.
- Given a photo without EXIF data, then date and GPS fields are left empty and the import continues.
- Given a HEIC photo from an iPhone, then its EXIF data is read the same way as a JPEG.
- Given a photo whose EXIF date is earlier than 1990 or in the future, then date_taken is stored and the photo is flagged date_suspect.

Sample EXIF output attached.""",
     "comments": ["BA: refined and agreed with the product owner. Ready for development."],
     "attachments": ["assets/sample_exif_output.txt"]},
    {"id": "S12", "epic": "E2", "summary": "One-time Vision API processing with cost tracking",
     "labels": ["phase-1", "backend", "ml"],
     "description": """As the product owner, I want each photo sent to the Vision API exactly once and the results stored locally, so that searches never cost money.

## Acceptance criteria
- Given an unprocessed photo, then labels, detected text and face boxes are stored and processed_by_api is set.
- Given a processed photo, then it is never sent again.
- Given a batch run, then the estimated and actual cost are shown before and after processing."""},

    # ---------------- E3 People (Phase 1) ----------------
    {"id": "S5", "epic": "E3", "summary": "Face detection and clustering",
     "labels": ["phase-1", "ml", "faces"],
     "description": """Group similar faces from the Vision API results into clusters that the family can name later. Clustering runs locally.""",
     "comments": [
         "Developer: open question - how many sample faces should a cluster preview show? 5 or 10? Also need a decision on the similarity threshold for merging clusters.",
         "Product owner: let's discuss next week.",
     ]},
    {"id": "S6", "epic": "E3", "summary": "Face labeling UI",
     "labels": ["phase-1", "ui", "faces"],
     "description": """Build a screen where users can name the people in photos. Mockup attached.""",
     "comments": ["Product owner: the kids will use this too, it has to be really easy."],
     "attachments": ["assets/face_labeling_mockup.png"]},
    {"id": "S13", "epic": "E3", "summary": "Manage people: add, rename, merge, remove",
     "labels": ["phase-1", "ui", "faces"],
     "description": """As a family member, I want to add, rename, merge and remove people, so that names stay correct as the family uses the app.

## Acceptance criteria
- Given two people that are the same person, when I merge them, then all their faces belong to one person.
- Given I remove a person, then their faces become Unknown; no photos are deleted.
- Given 15 tracked people, when I try to add another, then the app explains the limit."""},

    # ---------------- E4 Search and browse (Phase 1) ----------------
    {"id": "S7", "epic": "E4", "summary": "Search photos by person, date and location",
     "labels": ["phase-1", "ui", "search"],
     "description": """As a family member, I want to filter photos by person, date range and location, and combine these filters, so that I can quickly find photos such as 'Son in Austin in 2023'."""},
    {"id": "S8", "epic": "E4", "summary": "Gallery and photo detail view",
     "labels": ["phase-1", "ui"],
     "description": """Show photos as a thumbnail grid with a detail view showing date, location and people."""},

    # ---------------- E5 Duplicates and quality (Phase 2) ----------------
    {"id": "S14", "epic": "E5", "summary": "Review and remove duplicates",
     "labels": ["phase-2", "ui", "duplicates"],
     "description": """As a family member, I want to review flagged duplicates side by side and remove the copies I don't need, so that the library stays clean.

## Acceptance criteria
- Given a duplicate group, then all copies are shown side by side with size, date and source.
- Given I remove a copy, then it moves to the Windows Recycle Bin, never permanently deleted.
- Given a removed copy, then originals on the source drives are untouched."""},
    {"id": "S15", "epic": "E5", "summary": "Suggest the best shot from similar photos",
     "labels": ["phase-2", "ml", "quality"],
     "description": """Score sharpness, exposure and open eyes for burst and near-duplicate groups and suggest the best photo. The family makes the final choice."""},

    # ---------------- E6 Smart search and life events (Phase 2) ----------------
    {"id": "S16", "epic": "E6", "summary": "Natural language search",
     "labels": ["phase-2", "search", "ml"],
     "description": """As a family member, I want to type searches like 'New Year photos with Grandma', so that I don't need to use filters.

The query is translated into the same filters as the search screen. Only the query text is sent to the LLM, never photos."""},
    {"id": "S17", "epic": "E6", "summary": "Important dates and events",
     "labels": ["phase-2", "search"],
     "description": """As a family member, I want to record birthdays, anniversaries and trips, so that I can search 'our anniversaries' or 'Italy trip' without remembering dates."""},

    # ---------------- E7 Sharing and multi-user (Phase 3) ----------------
    {"id": "S18", "epic": "E7", "summary": "Export an album to a folder or zip",
     "labels": ["phase-3", "sharing"],
     "description": """Export selected photos to a folder or zip so they can be shared outside the app."""},
    {"id": "S19", "epic": "E7", "summary": "Family profiles with private and shared photos",
     "labels": ["phase-3", "multi-user"],
     "description": """Each family member gets a profile; photos can be private or shared with the family library."""},
    {"id": "S20", "epic": "E7", "summary": "Windows installer and auto-update for friends",
     "labels": ["phase-3", "distribution"],
     "description": """Signed Windows installer with auto-update so friends can install and keep the app current."""},

    # ---------------- E8 Memories and collages ----------------
    {"id": "S10", "epic": "E8", "summary": "Birthday collage helper",
     "labels": ["phase-1", "script"],
     "description": """Collect candidate photos for our son's 10th birthday collage: birthday photos from June 9 each year, family photos over the years, and solo portraits.""",
     "comments": ["Product owner: birthday photos should be June 9 only, exact date."]},
    {"id": "S21", "epic": "E8", "summary": "Collage layout builder and print export",
     "labels": ["phase-2", "ui"],
     "description": """Arrange selected photos into a collage template and export a print-ready PDF or image."""},
]

# (blocker, blocked): "S1 blocks S2"
BLOCKS = [
    ("S1", "S2"), ("S1", "S3"), ("S2", "S4"), ("S2", "S9"), ("S2", "S11"),
    ("S4", "S12"), ("S12", "S5"), ("S5", "S6"), ("S6", "S13"),
    ("S4", "S7"), ("S6", "S7"), ("S7", "S8"),
    ("S9", "S14"), ("S9", "S15"), ("S7", "S16"), ("S7", "S17"),
    ("S8", "S18"), ("S7", "S10"), ("S10", "S21"),
]

RELATES = [("S3", "S2"), ("S3", "S9"), ("S3", "S11"), ("S3", "S14")]

DEMO_TARGETS = {
    "Scenario 1 - BA agent, scope conflict": "S3",
    "Scenario 2 - BA agent, dependency awareness": "S6",
    "Scenario 3 - QA agent, test design": "S4",
}
