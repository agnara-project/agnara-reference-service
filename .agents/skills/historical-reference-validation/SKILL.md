---
name: historical-reference-validation
description: Operational workflow for auditing, validating, and verifying agnara-reference-service (#009) as the canonical integrating application for agnara==0.1.0a3.
---

# Historical Reference Validation Skill

Use this skill when auditing, validating, or extending **Agnara Historical Reference Application #009 (`agnara-reference-service`)**.

---

## 1. When to Use This Skill

Activate this skill whenever:
- Auditing the end-to-end integration of the five core reference concepts (#004–#008) in #009.
- Verifying the 8-layer educational pipeline:
  `Input` -> `Capability Contract` -> `Typed Validation` -> `Execution Plan` -> `Policy / Risk / Effects` -> `Dependency Resolution` -> `Domain Service` -> `Execution` -> `Outcome / Error` -> `Observability`.
- Verifying that execution plans are compiled Ahead-of-Time (AOT) via `ExecutionPlan.compile()`.
- Checking that Agnara runtime policies (`ScopePolicy`, `PaymentSpendingLimitPolicy`) are strictly demarcated from application domain rules.
- Ensuring the DI container lifecycle is properly managed via `DIContainer.aclose()`.
- Validating the 9 interactive scenarios executed by `app.py`.

---

## 2. Relevant Inputs & Architectural Boundaries

- **`domain.py`:** Pure immutable domain models (`Product`, `OrderItem`, `OrderRecord`, `InventoryReservation`, `PaymentAuthorization`).
- **`services.py`:** In-memory business repositories, simulators, and DI registry compilation.
- **`policies.py`:** Custom domain guardrails implementing `agnara.Policy` evaluated during runtime plan execution.
- **`capabilities.py`:** Public capability declarations registering the 6 core business operations.
- **`telemetry.py`:** Observers implementing the synchronous `TelemetryHook` protocol.
- **`service.py`:** High-level facade orchestrating execution plans with pre-compiled DI and context.
- **`app.py`:** Interactive CLI showcasing all 9 operational paths.

---

## 3. Ordered Implementation Workflow

### Step 1: Pinned Baseline & Environment Check
1. Ensure the Python environment runs CPython >= 3.14.
2. Verify exact framework version:
   ```python
   import agnara

   assert agnara.__version__ == "0.1.0a3"
   ```

### Step 2: 8-Layer Pipeline Verification
1. Verify each capability handler follows the 8 layers:
   - Layer 1 (Input): Caller provides raw dict or keyword arguments.
   - Layer 2 (Capability Contract): Capability identity and metadata parsed.
   - Layer 3 (Typed Validation): Agnara schema port validates types before handler invocation.
   - Layer 4 (Execution Plan): Pre-compiled `ExecutionPlan` routes the invocation.
   - Layer 5 (Policy / Risk / Effects): `ScopePolicy` and `PaymentSpendingLimitPolicy` evaluate; metadata remains inspectable.
   - Layer 6 (Dependency Resolution): `DIResolver` extracts services from `DIContainer`.
   - Layer 7 (Domain / Application Service): Pure domain logic executes against in-memory stores.
   - Layer 8 (Execution / Outcome / Observability): `Success[T]` or `Failure` returned; `TelemetryHook` observers record metrics.

### Step 3: Secret Protection & Security Redaction
1. Verify simulated payment references (`payment_ref="sim-ref-..."`) are sanitized before persistence.
2. Confirm raw payment references never appear in telemetry event records or audit logs.
3. Confirm `Failure.details` is an immutable `MappingProxyType`.

### Step 4: Quality Gate Verification
Execute the standard test suite and CLI runner:
```powershell
pytest -v
ruff check .
ruff format --check .
python app.py
```

---

## 4. Operational Boundaries & Negative Constraints

- **Do NOT upgrade Agnara:** Pinned strictly to `0.1.0a3`.
- **Do NOT add external web frameworks:** No FastAPI, Starlette, Flask, or HTTP servers.
- **Do NOT add databases or ORMs:** No SQLite, SQLAlchemy, PostgreSQL, or disk files.
- **Do NOT introduce real banking credentials:** Simulated test references only.
- **Do NOT leave BOM or mixed line endings:** Ensure clean UTF-8 encoding.

---

## 5. Validations & Definition of Done

The validation is complete when:
- [ ] All 24 unit and integration tests pass cleanly with 0 failures.
- [ ] `ruff check .` returns zero warnings.
- [ ] `ruff format --check .` confirms all files are properly formatted.
- [ ] `python app.py` executes all 9 scenarios successfully.
- [ ] Zero secret leakage is confirmed in telemetry and audit logs.
