---
name: detect-scope-conflicts
description: Find contradictions between a ticket and the roadmap phases, related stories, attachments and comments in the PSA project. Use when a ticket mentions behaviour that may belong to another phase or story, or when attachments exist.
---

# Detect scope conflicts

## Compare these pairs
1. **Ticket vs roadmap phase.** Check the "Phase boundaries that matter for stories" section of the Product Vision and Roadmap page. Example: removing duplicates is Phase 2; Phase 1 only flags them.
2. **Ticket vs related stories.** If a related story owns the behaviour, the ticket must reference it rather than duplicate or contradict it.
3. **Ticket vs attachments.** Options, fields or numbers visible in a wireframe or mockup but absent from the description, or the reverse.
4. **Ticket vs comments.** Product owner remarks that add requirements (for example "kids should be able to use it").
5. **Ticket vs principles and NFRs.** For example: originals are never changed, nothing is permanently deleted, usable by a 10-year-old.

## For each conflict report
- **What**: the two statements that disagree, quoted briefly.
- **Sources**: where each statement comes from.
- **Impact**: what goes wrong if built as written.
- **Recommendation**: the change to make, and which story should own the behaviour (by key).

Never silently drop a requirement. Move it to the right phase or story and say so.
