# Public API Boundary & Discarded Capabilities Audit

> **Historical Reference Application #009:** `agnara-reference-service`
> **Framework:** `agnara==0.1.0a3` | **Runtime:** CPython >= 3.14

---

## 1. Verified Public APIs in `agnara==0.1.0a3`

The following public symbols and features were inspected directly in the published distribution of `agnara==0.1.0a3` and are used within this reference application:

| Module / Package | Public Symbols Used | Architectural Purpose |
| ---------------- | ------------------- | --------------------- |
| `agnara.application` | `Agnara` | Composition root, capability authoring, and registration freeze (`compile()`). |
| `agnara.capability.identity` | `CapabilityId` | Structured namespaced identifier (`namespace.name`). |
| `agnara.capability.definition` | `CapabilityDefinition` | Full capability definition declaring handler, metadata, and policies. |
| `agnara.capability` | `Risk`, `StandardEffect`, `Idempotency`, `Confirmation` | Standardized operational metadata enums. |
| `agnara.core.di` | `DIRegistry`, `DIContainer`, `Scope`, `provider`, `compile_dag` | Dependency injection container with singleton and invocation scopes. |
| `agnara.execution.context` | `ExecutionContext` | Per-invocation runtime environment holding `tracking_id`, `principal`, and `deadline`. |
| `agnara.execution.invocation` | `Invocation` | Protocol-neutral request carrying `capability_id`, `payload`, `metadata`, and `deadline`. |
| `agnara.execution.plan` | `ExecutionPlan` | Ahead-of-time compiled capability plan validating signatures, dependencies, schemas, and hooks. |
| `agnara.execution.result` | `CanonicalResult`, `Success`, `Failure`, `FailureCode` | Transport-neutral outcome envelope with immutable details (`MappingProxyType`). |
| `agnara.execution.runtime` | `invoke`, `invoke_result`, `_tracking_id` | Runtime executor enforcing policies, timeouts, and exception sanitization. |
| `agnara.execution.telemetry`| `TelemetryHook`, `InvocationStartEvent`, `InvocationTerminalEvent` | Synchronous lifecycle observer protocol with nanosecond timing and UUID4 pairing. |
| `agnara.policy` | `Policy`, `PolicyResult`, `PolicySuccess`, `PolicyFailure`, `ScopePolicy`, `Principal` | Declarative guardrails and security verification. |
| `agnara.schema.standard` | `StandardSchemaAdapter` | Type introspection and runtime input validation. |
| `agnara.errors` | `DefinitionError`, `ValidationError`, `InvocationError`, `PolicyDeniedError` | Protocol-neutral error hierarchy. |

---

## 2. Discarded Capabilities & Architectural Adaptations

In strict adherence to the project rules, speculative or unreleased features were **not** faked as official Agnara features:

### 1. Built-in Workflow Engine in Core
- **Initial Idea:** Use an `@app.workflow` decorator or state machine in Agnara core.
- **Verification in a3:** Inspected `agnara` package. There is no workflow engine in core; Agnara 0.1.0a3 focuses on compiling and executing individual capabilities (`ExecutionPlan`).
- **Decision / Adaptation:** The 6 capabilities are declared cleanly as Agnara capabilities, and orchestrated by `ReferenceOrderService`.

### 2. Built-in OpenTelemetry SDK / OTLP Exporter in Core
- **Initial Idea:** Built-in OTLP network exporter or Jaeger integration.
- **Verification in a3:** Agnara core does not bundle external OTel packages. Observability is provided via the in-process `TelemetryHook` protocol.
- **Decision / Adaptation:** Implemented `ServiceTelemetryCollector` and `AuditLoggingHook` following the real `TelemetryHook` protocol.

### 3. Distributed W3C `traceparent` Header Parsing in Core
- **Initial Idea:** Automatic HTTP header extraction of distributed trace context.
- **Verification in a3:** Agnara core is transport-neutral and does not parse HTTP headers. `ExecutionContext` accepts `tracking_id: str | None`.
- **Decision / Adaptation:** Correlation across steps is achieved by passing the caller's `tracking_id` into each invocation context.

### 4. Automatic Deserialization from Dict to Dataclass in `StandardSchemaAdapter`
- **Initial Idea:** Passing raw dictionaries into dataclass-annotated parameters.
- **Verification in a3:** `StandardSchemaAdapter.compile(Dataclass)` produces `DataclassSchema`, which strictly enforces `isinstance(val, cls)`.
- **Decision / Adaptation:** Handler parameters accept primitives and typed collections for wire-payload compatibility, while domain return values use typed dataclasses.

### 5. `@app.capability(policies=...)` Parameter
- **Initial Idea:** Passing policies directly to `@app.capability(policies=[...])`.
- **Verification in a3:** `@app.capability` in `agnara.application` does not accept a `policies` parameter.
- **Decision / Adaptation:** Handlers are declared with metadata, and capabilities with policies are instantiated via `CapabilityDefinition.declare(..., policies=...)` and registered on `app.capabilities`.

### 6. Asynchronous / Generator Telemetry Hooks
- **Verification in a3:** `ExecutionPlan.__post_init__` strictly requires telemetry hooks to be synchronous and non-generating.
- **Decision / Adaptation:** All telemetry observers are strictly synchronous callables.
