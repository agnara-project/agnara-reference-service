## Description

Briefly describe the change, its pedagogical objective, and why it is necessary.

---

## Historical Baseline Confirmation

This repository is **Agnara Historical Reference Application #009**, pinned to `agnara==0.1.0a3` on **CPython >= 3.14**.

- [ ] I confirm this PR does NOT upgrade `agnara` or modify `requirements.txt` / `pyproject.toml` pins.
- [ ] I confirm this PR does NOT introduce speculative APIs from unreleased branches (`main`/`develop`).
- [ ] I confirm this PR preserves the separation between framework policies (`ScopePolicy`), custom policies (`PaymentSpendingLimitPolicy`), and application domain rules.
- [ ] I confirm this PR preserves strict secret redaction (no PANs, raw tokens, or credentials in logs/telemetry).
- [ ] I confirm this PR maintains zero external framework dependencies (no FastAPI, Starlette, SQLite, SQLAlchemy, etc.).

---

## Scope of Changes

- [ ] Domain models & service contracts (`domain.py`, `services.py`)
- [ ] Policy definitions & guardrails (`policies.py`)
- [ ] Capability declarations (`capabilities.py`)
- [ ] Telemetry & observability (`telemetry.py`)
- [ ] Service orchestrator facade (`service.py`)
- [ ] CLI application (`app.py`)
- [ ] Test coverage (`tests/`)
- [ ] Documentation (`README.md`, `ARCHITECTURE.md`, `AGENTS.md`, `docs/`)
- [ ] Agent context & skills (`.agents/`)
- [ ] CI/CD automation (`.github/`)

---

## Definition of Done (DoD) Checklist

- [ ] `pytest -v` exits with code `0` (all 24+ tests passing).
- [ ] `ruff check .` exits with code `0` (zero linting errors).
- [ ] `ruff format --check .` exits with code `0` (all code properly formatted).
- [ ] `python app.py` runs all 9 scenarios end-to-end and exits with code `0`.
- [ ] Zero UTF-8 Byte Order Marks (BOM) in any files.
- [ ] Documentation accurately reflects what `agnara==0.1.0a3` supports vs does not support.
