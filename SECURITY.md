# Security Policy

## Supported Versions

This repository is **Historical Reference Application #009** for **`agnara==0.1.0a3`**. It is permanently pinned to that historical release.

| Version | Supported | Notes |
| ------- | --------- | ----- |
| `agnara==0.1.0a3` | :white_check_mark: | Historical reference baseline |
| `< 0.1.0a3` | :x: | Not supported in this reference app |
| `> 0.1.0a3` | :x: | Newer releases are covered in subsequent reference apps |

---

## Secret & PII Handling Invariants

This reference application demonstrates strict zero-leakage security boundaries:

1. **Payment References & Financial Simulation:**
   - Raw payment references (`payment_ref`), simulated credentials, and cardholder account identifiers must never be stored in plain text logs, emitted in telemetry events, or returned in diagnostic error payloads.
   - All diagnostic representations must use the sanitization helper (`mask_secret()`) displaying at most prefix and last 4 characters (e.g., `sim-***4242`).
   - Payment operations are strictly fictional in-memory simulations; no real financial institutions, networks, or account numbers are touched.

2. **Telemetry Invariant:**
   - Observers implementing `agnara.execution.telemetry.TelemetryHook` receive only invocation metadata (`capability_id`, `tracking_id`, `invocation_id`, `duration_ns`, `outcome`).
   - Telemetry hooks never receive raw invocation payloads or sensitive business inputs.

3. **Exception Sanitization:**
   - Runtime execution errors caught by `invoke_result` redact unexpected traceback internals into canonical `FailureCode.INTERNAL_FAILURE` envelopes.
   - Failure details returned to external callers are guarded using read-only `MappingProxyType` structures.

---

## Reporting a Vulnerability

If you discover a potential security issue in the reference application or underlying Agnara framework, please do not file a public GitHub issue. Send security advisories to:

- **Security Team:** `security@agnara.dev`
- **PGP Key:** Available upon request or at standard project security endpoints.
