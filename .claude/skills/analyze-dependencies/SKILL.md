---
name: analyze-dependencies
description: Analyse a Jira ticket's dependency chain - blocking tickets, their status and their unresolved questions - and explain the risk to the ticket under review. Use whenever a ticket has links.
---

# Analyse dependencies

1. List every link with relationship and status.
2. For each **"is blocked by"** ticket that is not Done:
   - State the risk in one sentence.
   - Extract open questions from its comments, quoting the key words.
   - Check whether the ticket under review or its attachments already assume an answer. If they do, flag it as an **assumption conflict** (for example a mockup showing 6 sample faces while the blocker is still deciding between 5 and 10).
3. For **"relates to"** tickets, note anything that changes the scope of the ticket under review.
4. Recommend one of:
   - Wait for the blocker.
   - Proceed with an explicit assumption, which the product owner must confirm.
   - Split the story so part of it can start now.

## Output
```
| Linked ticket | Relationship | Status | Risk / open question |
|---------------|--------------|--------|----------------------|
```
