---
name: testing
description: Testing methodology, negative evidence verification, and quality gates for agnara-reference-service (#009).
---

# Testing Skill

Use this skill when authoring, modifying, or executing tests in **Agnara Historical Reference Application #009 (`agnara-reference-service`)**.

---

## 1. When to Use This Skill

Activate this skill whenever:
- Adding or modifying unit and integration tests in `tests/`.
- Verifying isolated capability contracts or end-to-end service facade flows.
- Testing policy rejections (`FailureCode.FORBIDDEN`), inventory conflicts (`FailureCode.CONFLICT`), invalid input (`FailureCode.INVALID_INPUT`), or timeouts (`FailureCode.TIMEOUT`).
- Verifying zero secret leakage in audit logs and telemetry events.
- Running the complete verification suite before historical freezing.

---

## 2. Relevant Inputs

- **`tests/test_compilation.py`:** Ahead-of-Time plan compilation, DI graph resolution, protected parameter injection, and hook protocol validation.
- **`tests/test_capabilities_isolated.py`:** Direct capability invocation tests for all 6 operations.
- **`tests/test_service_e2e.py`:** Multi-step order lifecycle, conflict handling, and deadline timeout tests.
- **`tests/test_policies_and_guardrails.py`:** ScopePolicy enforcement, spending limit evaluation, and cancellation reason length checks.
- **`tests/test_telemetry_and_observability.py`:** TelemetryHook observer events, monotonic duration measurement, and tracking ID filtering.
- **`tests/test_security_redaction.py`:** Secret masking, log redaction, and `Failure.details` immutability.

---

## 3. Ordered Implementation Workflow

### Step 1: Self-Contained Async Execution
1. Do not install or require external pytest plugins (such as `pytest-asyncio`).
2. Wrap asynchronous test code in synchronous test functions using `asyncio.run(_run())`.
3. Keep test fixtures and state isolated to prevent test contamination.

### Step 2: Positive & Negative Contract Assertions
1. Assert positive outcomes produce `Success[T]` with validated domain models.
2. Assert negative paths produce typed `Failure` instances with expected `FailureCode`:
   - Missing required scopes: `FailureCode.FORBIDDEN`
   - Spending limit exceeded: `FailureCode.FORBIDDEN`
   - Insufficient inventory: `FailureCode.CONFLICT`
   - Invalid or empty payload: `FailureCode.INVALID_INPUT`
   - Deadline expiration: `FailureCode.TIMEOUT`
   - Order not found: `FailureCode.NOT_FOUND`
3. Verify failure immutability (`isinstance(res.details, MappingProxyType)`).

### Step 3: Verification Execution
Run the verification suite:
```powershell
pytest -v
ruff check .
ruff format --check .
```

---

## 4. Operational Boundaries & Negative Constraints

- **Zero External Dependencies:** Only rely on standard `pytest` and Python standard library `asyncio`.
- **No Mocking of Core Runtime:** Test against real Agnara `ExecutionPlan`, `DIContainer`, `ExecutionContext`, and `invoke_result()`.
- **No Speculative APIs:** Test only features available in `agnara==0.1.0a3`.

---

## 5. Validations & Definition of Done

The testing workflow is complete when:
- [ ] All test files collect and pass with 0 failures in `pytest -v`.
- [ ] Both positive support and negative error paths are verified.
- [ ] Ruff reports 0 linting and 0 formatting errors.
