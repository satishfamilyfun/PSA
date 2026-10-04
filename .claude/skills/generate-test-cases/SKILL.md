---
name: generate-test-cases
description: Design test cases for a PSA story from its acceptance criteria - Gherkin scenarios, a coverage table and edge cases taken from attachments and the Test Strategy page - and flag gaps. Use for QA test design on ready-for-dev stories.
---

# Generate test cases

## 1. Coverage first
Map every acceptance criterion to at least one scenario. Build this table:
```
| AC # | Acceptance criterion (short) | Scenarios | Covered? |
```

## 2. Edge cases
Add scenarios from:
- The attachments (each sample record or design element that suggests a case).
- The Test Strategy page fixture list: HEIC, photos without GPS, scanned photos with wrong dates, WhatsApp images with stripped EXIF, screenshots, duplicates, corrupt files.
- Error handling: unreadable files, missing permissions, interrupted runs.

## 3. Gaps
A gap is input the story will receive, shown in an attachment or the fixture list, that **no acceptance criterion covers**. List each gap with a proposed criterion for the BA. Also flag criteria that are ambiguous or untestable.

## 4. Gherkin format
```gherkin
Feature: <story summary> (<KEY>)

  Scenario: <behaviour>  # covers AC1
    Given ...
    When ...
    Then ...
```
Use Scenario Outline with Examples for data variations (for example several file types).

## 5. Safety checks
Any scenario that writes files must also assert that the original file is unchanged.
