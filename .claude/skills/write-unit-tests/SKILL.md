---
name: write-unit-tests
description: Write focused pytest unit tests for PSA Python code - happy path, edge cases and errors, using small fixtures and never real family photos. Use when a task asks for tests or for small helper functions with tests.
---

# Write unit tests

1. One test file per module: `app/tests/test_<module>.py`.
2. Name tests by behaviour: `test_returns_none_when_gps_missing`, not `test_1`.
3. For each function cover:
   - the happy path,
   - each edge case listed in the plan task and in the QA scenarios (missing values, HEIC, suspect dates),
   - invalid input (wrong type or malformed string) if the function is meant to handle it.
4. Use `pytest.mark.parametrize` for several similar inputs.
5. Build test data in code or with `tmp_path`; never read files outside the repo.
6. One assert per behaviour where practical; compare floats with `pytest.approx`.
7. Run `python -m pytest app -q` and report the count of passed and failed tests in your result file.
