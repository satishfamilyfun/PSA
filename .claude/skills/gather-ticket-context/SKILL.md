---
name: gather-ticket-context
description: Collect complete context for a Jira ticket in the PSA project - description, comments, attachments, linked tickets with their open questions, and the relevant Confluence knowledge base pages. Use at the start of any ticket review, refinement or test design task.
---

# Gather ticket context

Follow these steps in order. Do not skip steps; missing context is the main cause of poor reviews.

## 1. Ticket bundle (one call)
Call `mcp__psa__get_ticket_bundle` with the ticket key. It returns the description, comments, attachments (saved locally) and linked tickets. Blocking and related tickets include their description and comments.

## 2. Attachments
- For every image listed, open the saved file with the **Read** tool and note each visible element (fields, options, buttons, numbers, notes).
- Text attachments are already included in the bundle; read them fully.
- Record every difference between an attachment and the description.

## 3. Linked tickets
For each linked ticket note: relationship, status, and any unanswered question in its comments. A blocker whose status is not Done is a dependency risk.

## 4. Knowledge base (Confluence space PSA)
- Call `mcp__atlassian__getAccessibleAtlassianResources` once to get the cloudId for satishfamilyfun.atlassian.net.
- Use `mcp__atlassian__searchConfluence` with CQL such as `space = PSA AND title ~ "Roadmap"`, then `mcp__atlassian__getConfluenceContent` for the pages you need.
- Read only the pages relevant to your role (see your agent instructions). Do not read all 11 pages.

## 5. Context summary
Before analysing, write a short internal summary with these headings: Ticket, Attachments, Linked tickets, Knowledge base facts that apply. Every later finding must trace back to one of these sources; cite the source (for example "wireframe", "PSA-6 comment", "Roadmap page").
