# Engineering Standards

## Code
- Python 3.11+ for the core service; type hints and docstrings on public functions.
- Formatting with black and ruff; tests with pytest.
- TypeScript and React for the UI.

## Git workflow
- Branch per story: feature/PSA-<number>-short-name.
- Conventional Commits, for example feat(import): copy photos into date folders (PSA-3).
- Pull requests need passing tests and one review.

## Definition of Done
- Acceptance criteria met and tested.
- Code reviewed and merged to main.
- No failing tests; new code has unit tests.
- User-facing text reviewed for plain language.
- Jira ticket updated and moved to Done.
