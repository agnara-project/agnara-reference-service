# Contributing to Agnara Historical Reference Application #009

## Historical / Frozen Status

This repository is **Agnara Historical Reference Application #009**, strictly pinned to **`agnara==0.1.0a3`** on **CPython >= 3.14**.

As a historical reference artifact:
- **No API Modernization:** Code must not be updated to use APIs introduced in releases after `0.1.0a3`.
- **Educational Value:** Contributions are limited to correcting factual inaccuracies in documentation, fixing reproducible bugs under Python 3.14 + Agnara 0.1.0a3, or improving explanation clarity.
- **Dependency Discipline:** No new runtime dependencies may be introduced.

---

## Local Development & Validation

### Setup
```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e ".[dev]"
```

### Verification Commands
```powershell
# Format and lint checks
ruff check .
ruff format --check .

# Automated test suite
pytest -v

# Interactive demonstration
python app.py
```
