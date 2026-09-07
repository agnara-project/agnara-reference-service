# Changelog

All notable changes to **Agnara Historical Reference Application #009 (`agnara-reference-service`)** are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to historical version pinning against `agnara==0.1.0a3`.

---

## [0.1.0] - 2026-09-07

### Added
- Canonical integrating application implementing a complete Order Management Service (OMS).
- 6 core business capabilities:
  - `catalog.get_product`: Typed read operation with `Risk.LOW` and `StandardEffect.READ`.
  - `inventory.reserve`: Stateful stock reservation with `Risk.MEDIUM` and `StandardEffect.DATABASE_WRITE`.
  - `payments.authorize`: Financial authorization with `Risk.HIGH`, `StandardEffect.FINANCIAL_WRITE`, and `PaymentSpendingLimitPolicy`.
  - `orders.create`: Multi-step transactional order orchestration with `Risk.HIGH`.
  - `orders.get`: Order retrieval with `Risk.LOW` and `StandardEffect.READ`.
  - `orders.cancel`: Destructive lifecycle cancellation with `Risk.CRITICAL`, `StandardEffect.DESTRUCTIVE`, and `OrderCancellationPolicy`.
- 8-layer educational pipeline integrating:
  1. Capabilities
  2. Typed Contracts
  3. Dependency Injection (DIRegistry & DIContainer)
  4. Execution Plans (ExecutionPlan.compile)
  5. Policies, Risk, and Effects
  6. Execution Runtime (invoke_result)
  7. Canonical Outcomes & Failure Codes
  8. Telemetry Hooks (TelemetryHook & ServiceTelemetryCollector)
- Comprehensive test suite covering plan compilation, isolated capabilities, end-to-end service orchestration, policy guardrails, observability, and secret redaction.
- Interactive CLI application (`app.py`) demonstrating 9 real-world operational scenarios.
- Complete documentation suite (`README.md`, `ARCHITECTURE.md`, `AGENTS.md`, `docs/architecture-guide.md`, `docs/public-api-boundary.md`).
