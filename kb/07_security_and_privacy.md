# Security and Privacy

## Data handling
- Photos, faces and metadata are stored only on the local machine.
- The Vision API receives each photo once. Use a provider setting that does not retain or train on the images where available.
- Phase 2 natural language search sends only the query text, never photos or face data.
- API keys are stored in the Windows Credential Manager, never in plain files.

## Face data
- Face embeddings are biometric data. They stay local and are deleted when a person is removed, unless the user chooses to keep them.
- Children's faces get the same protection; no face data is ever shared or exported automatically.

## Safety rules
- The app never permanently deletes files (ADR-007).
- Originals on source drives are read-only to the app.

## Phase 3 considerations
- Profiles add private photos; child profiles cannot change people or delete anything.
- Sharing exports are explicit, user-initiated actions only.
