# Contributing to Review Studio

Thank you for helping improve Review Studio.

## Development Principles

- Keep GUI code thin; business workflows belong in services/view models.
- Do not hardcode templates in GUI code.
- Protect user work: prefer atomic writes, autosave, and safe fallbacks.
- Add or update tests for behavior changes.
- Use type hints and docstrings for public modules/classes/functions.
- Avoid unrelated file rewrites.

## Local Setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .[dev]
```

## Checks

```bash
QT_QPA_PLATFORM=offscreen PYTHONPATH=src python -m unittest discover -s tests
ruff check src tests
mypy src tests
```

## Pull Request Expectations

Before submitting a pull request:

1. Run the test suite.
2. Run lint/type checks when available.
3. Document user-visible changes.
4. Explain architectural tradeoffs for significant changes.
5. Keep changes focused on the stated problem.

## Security and Data Safety

Review Studio stores user-created review data locally. Changes to persistence, export, or
template loading should be reviewed carefully for data-loss and security risks.