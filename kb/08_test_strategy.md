# Test Strategy

## Test levels
| Level | Scope | Tools |
|-------|-------|-------|
| Unit | Components such as ExifReader, DuplicateDetector, Copier | pytest |
| Integration | Import pipeline end to end on a fixture folder | pytest with temporary folders |
| UI | Wizard, labeling and search flows | Playwright |
| Acceptance | Each story's Given/When/Then criteria | Gherkin scenarios mapped to tests |
| Usability | A family member (including a child) completes key tasks | Moderated session |

## Test data
A fixture library of about 50 photos covering: iPhone JPEG and HEIC, Android JPEG, photos without GPS, scanned photos with wrong dates, WhatsApp images with stripped EXIF, screenshots, exact and near duplicates, and corrupt files.

## Rules
- Every acceptance criterion has at least one test case.
- Edge and error cases are required, not optional.
- Tests never touch real family photos; use the fixture library.
- Any test that removes files must verify originals are untouched.

## Test case format
Gherkin: Feature, Scenario, Given, When, Then. Each scenario references its story key.
