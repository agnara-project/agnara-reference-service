# Agent Skills & Operational Registry

This directory contains specialized agent context and operational skills for **Agnara Historical Reference Application #009 (`agnara-reference-service`)**.

## Pinned Baseline
- **Repository:** `agnara-project/agnara-reference-service`
- **Designation:** Agnara Historical Reference Application #009
- **Framework Version:** Strictly pinned to `agnara==0.1.0a3`
- **Python Version:** CPython >= 3.14
- **Status:** Historical / Frozen

## Integrating Purpose
As Reference Application #009, this repository serves as the definitive synthesis of the five foundational reference applications:
1. `#004 agnara-capability-basics`: Capability definitions, metadata, inputs, and handler contracts.
2. `#005 agnara-execution-runtime`: Execution plan compilation, execution context, outcomes, and timeout cancellation.
3. `#006 agnara-typed-contracts`: Typed schema validation, failure codes, and protected DI parameter extraction.
4. `#007 agnara-policy-guardrails`: Declarative vs enforced policies, ScopePolicy, and custom domain guardrails.
5. `#008 agnara-observable-workflows`: TelemetryHook observers, monotonic latency measurement, and correlation tracking.

## Critical Agent Invariants
1. **Never upgrade Agnara:** Under no circumstances should `pyproject.toml` or `requirements.txt` reference versions later than `0.1.0a3` or unreleased git branches.
2. **Strict 3-Tier Architecture:** Maintain clean separation between Agnara framework abstractions, application domain logic, and in-memory infrastructure adapters.
3. **No External Framework Dependencies:** Keep services and repositories as in-memory Python structures. Do NOT introduce FastAPI, Flask, Starlette, SQLite, SQLAlchemy, or Docker.
4. **Strict Secret Redaction:** Payment references, PANs, credentials, and tokens must never pass into logs or telemetry events.
5. **Preserve CPython 3.14+ Compatibility:** Maintain modern Python 3.14 idioms, including immutable slots dataclasses and monotonic loop timing.
6. **Zero-Warning Quality Gates:** Verify all tests and linters pass before completing any task:
   ```powershell
   pytest -v
   ruff check .
   ruff format --check .
   python app.py
   ```
