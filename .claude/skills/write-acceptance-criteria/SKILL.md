---
name: write-acceptance-criteria
description: Rewrite a PSA user story and write testable Given/When/Then acceptance criteria, including edge and error cases, plus clarifying questions. Use when refining a story or when acceptance criteria are missing or weak.
---

# Write acceptance criteria

## User story
`As a [persona from the Personas page], I want [capability], so that [benefit].`

## Rules for criteria
- Format: **Given** [context], **when** [action], **then** [observable result].
- One behaviour per criterion; observable and testable without asking the author.
- Cover: happy path, edge cases, error handling, and the safety principles (originals untouched, no permanent deletion).
- Use the vocabulary from the Glossary page (master library, source, duplicate, tracked person, Unknown).
- Where an answer is pending, write the criterion with a clearly marked assumption: `[Assumption - confirm: ...]`.
- Behaviour belonging to another phase is not written as a criterion; add a line "Out of this story: ... (see KEY)".

## Clarifying questions
Number them. Each question names who should answer (usually the product owner) and offers options where possible, for example "Q2: Skip screenshots by default, or ask each time? (product owner)".

## Jira description template
```
## User story
As a ..., I want ..., so that ...

## Acceptance criteria (draft - pending answers to the questions in the BA comment)
- Given ..., when ..., then ...

## Out of this story
- ... (see KEY)

## Original description
<keep the original text unchanged>
```
