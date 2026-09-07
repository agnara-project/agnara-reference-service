# AGENTS.md — Operational Manual for Autonomous AI Agents

> **Audience:** Claude Code, OpenAI Codex, Antigravity, and other autonomous AI coding agents inspecting, maintaining, or extending this codebase.
> **Role:** Single source of operational truth for machine agents. For human-oriented documentation, see `README.md`.

---

## 1. Project Identity & Historical Context

- **Repository:** `agnara-project/agnara-reference-service`
- **Designation:** **Agnara Historical Reference Application #009**
- **Framework Version:** Strictly pinned to **`agnara==0.1.0a3`**
- **Python Version:** **CPython >= 3.14**
- **Status:** **Historical / Frozen**
- **Mission:** Serve as the canonical integrating application demonstrating how to construct a small, professional Order Management Service using the public capabilities of Agnara 0.1.0a3.

---

## 2. Inviolable Architectural Constraints

1. **Do Not Upgrade Agnara:** Under no circumstances should `pyproject.toml` or `requirements.txt` be altered to reference versions later than `0.1.0a3` or development branches (`main`/`develop`).
2. **Do Not Invent Speculative APIs:** Only use the actual public API surface present in `agnara==0.1.0a3`.
3. **No External Framework Dependencies:** Keep services and repositories as in-memory Python structures.
4. **Strict Secret Redaction:** Payment tokens, credentials, and PANs must never pass into logs or telemetry events.
5. **Preserve CPython 3.14+ Compatibility:** Maintain strict compatibility with modern Python 3.14 idioms, including immutable slots dataclasses.
6. **Separation of Concerns:** Keep domain entities, in-memory adapters, capability declarations, policy evaluations, and the service orchestrator strictly decoupled.

---

## 3. Codebase Structure & Ownership

```
agnara-reference-service/
├── .github/workflows/ci.yml       # GitHub Actions CI (Python 3.14 on Ubuntu & Windows)
├── docs/
│   ├── architecture-guide.md      # Deep-dive guide into the 8-layer educational pipeline
│   └── public-api-boundary.md     # Verified public APIs vs discarded capabilities audit
├── AGENTS.md                      # Operational instructions for AI agents (this file)
├── ARCHITECTURE.md                # System architecture & integration specification
├── CHANGELOG.md                   # Historical release ledger
├── CONTRIBUTING.md                # Contribution rules under Historical/Frozen status
├── LICENSE                        # Apache 2.0 License
├── SECURITY.md                    # Security policy & secret protection guidelines
├── pyproject.toml                 # Hatchling build configuration & dev dependencies
├── requirements.txt               # Exact pinned core dependency (agnara==0.1.0a3)
├── domain.py                      # Pure domain models (Product, OrderItem, OrderRecord, etc.)
├── services.py                    # In-memory services (Catalog, Inventory, Payment, Order, Audit)
├── policies.py                    # Custom guardrail policies (SpendingLimit, CancellationPolicy)
├── capabilities.py                # Capability declarations for all 6 operations
├── telemetry.py                   # Real TelemetryHook observers (ServiceTelemetryCollector, AuditLoggingHook)
├── service.py                     # ReferenceOrderService facade orchestrating invocations
├── app.py                         # Interactive CLI runner showcasing all 9 operational scenarios
└── tests/
    ├── __init__.py
    ├── test_compilation.py        # Plan compilation, DI graph verification, schema adapter
    ├── test_capabilities_isolated.py # Isolated testing of all 6 capabilities
    ├── test_service_e2e.py        # Full end-to-end happy path & multi-step flows
    ├── test_policies_and_guardrails.py # Scope policies, spending limit policy, cancellation guardrails
    ├── test_telemetry_and_observability.py # TelemetryHook events, latency, correlation
    └── test_security_redaction.py # Zero secret leakage, PII masking, failure immutability
```

---

## 4. Verification Protocol

Before finishing any task or committing changes, run:
```powershell
pytest -v
ruff check .
ruff format --check .
python app.py
```
Ensure all tests pass with 0 failures and ruff returns 0 lint or format warnings.
