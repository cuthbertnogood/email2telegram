---
name: pytest-local
description: Run and extend pytest for email2telegram (sys.path via tests/conftest.py, asyncio tests, Dummy* fakes). Use when editing tests/, fixing test failures, or adding coverage for parser, pipeline, state, message_format.
---

# Pytest local (email2telegram)

## Run

```bash
python3 -m pytest -q
python3 -m pytest -q tests/test_pipeline.py
python3 -m pytest -q tests/test_pipeline.py::test_run_delivery_cycle_happy_path
```

## Layout

- `tests/conftest.py` inserts `src/` into `sys.path` — imports mirror runtime: `from pipeline import run_delivery_cycle`, not `from src.pipeline`.
- Async tests: `pytest.mark.asyncio` + `async def` (see `tests/test_pipeline.py`).

## Patterns in this repo

- **Fakes:** `DummyClient`, `DummyState`, `DummyBot` in `test_pipeline.py` for IMAP/Telegram boundaries.
- **Parser / format:** `test_parser.py`, `test_message_format.py` use bytes fixtures and edge-case headers.
- **State:** `test_state.py` for file-backed store behavior.

## Do not

- Add integration tests that hit real IMAP or Telegram APIs unless the user explicitly requests it and provides env/credentials handling.

## After code changes

- If you change delivery or parsing behavior, update or add tests in the closest matching `tests/test_*.py` file.
