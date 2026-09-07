# Architecture Guide: Building a Professional Service with Agnara 0.1.0a3

> **Historical Reference Application #009:** `agnara-reference-service`
> **Question Answered:** *"I already learned the individual pieces in #004 through #008; how do I build a small, professional application with them?"*

---

## 1. The 8-Layer Educational Architecture

In enterprise service design, application code must remain decoupled from communication transports (HTTP, WebSockets, gRPC, CLI) and framework runtime machinery.

Agnara achieves this through an explicit 8-layer unidirectional execution pipeline:

```
+-----------------------------------------------------------------------------------+
|                           THE 8-LAYER INTEGRATION PIPELINE                        |
+-----------------------------------------------------------------------------------+

 1. CAPABILITIES
    Pure domain intent declared as transport-neutral units of execution.
    Registered on an Agnara authoring surface with unique CapabilityId.
          │
          ▼
 2. TYPED CONTRACTS
    Python type hints compiled into immutable TypeSchemas via StandardSchemaAdapter.
    Validates primitive parameters, lists, dicts, and return contracts.
          │
          ▼
 3. DEPENDENCY INJECTION (DI)
    In-memory repositories and gateways registered in DIRegistry.
    Resolved dynamically and cleaned up via DIContainer per invocation scope.
          │
          ▼
 4. EXECUTION PLANS
    Ahead-of-time plan compilation via ExecutionPlan.compile.
    Validates complete dependency DAG, protected parameters, and observer contracts.
          │
          ▼
 5. POLICIES / RISK / EFFECTS
    Machine-readable Risk tiers, StandardEffect classification, and runtime Policy
    evaluators (ScopePolicy, PaymentSpendingLimitPolicy, OrderCancellationPolicy).
          │
          ▼
 6. EXECUTION RUNTIME
    Runtime invocation using ExecutionContext holding tracking_id and principal.
    Managed execution with timeout/deadline enforcement.
          │
          ▼
 7. OUTCOMES / ERRORS
    Protocol-neutral CanonicalResult envelopes: Success(value) vs Failure(code, msg).
    Semantic failure categorization (INVALID_INPUT, FORBIDDEN, CONFLICT, TIMEOUT).
          │
          ▼
 8. OBSERVABILITY & TELEMETRY
    In-process TelemetryHook lifecycle observers (InvocationStartEvent, InvocationTerminalEvent).
    High-resolution monotonic duration (duration_ns), UUID4 invocation pairing, and secret redaction.
```

---

## 2. Layer-by-Layer Breakdown

### Layer 1: Capabilities
Business operations are declared in `capabilities.py` without coupling to HTTP routers or web controllers. Handlers are ordinary Python functions (`get_product`, `reserve_inventory`, `authorize_payment`, `create_order`, `get_order`, `cancel_order`).

### Layer 2: Typed Contracts
Every capability handler declares explicit type annotations. At plan compilation time, `StandardSchemaAdapter` introspects the parameters and compiles validation schemas. At runtime, incoming payloads are strictly validated before the handler is invoked.

### Layer 3: Dependency Injection
Services (`CatalogRepository`, `InventoryService`, `PaymentGateway`, `OrderRepository`, `AuditLogger`) are registered into `DIRegistry` via `@provider(scope=Scope.SINGLETON)`. The runtime container (`DIContainer`) automatically resolves them to handler parameters.

### Layer 4: Execution Plans
Rather than inspecting functions on every incoming request, Agnara compiles an immutable `ExecutionPlan` once at startup. The plan computes required inputs, dependency graphs, and hook chains.

### Layer 5: Policies, Risk & Effects
Each capability declares its operational metadata:
- `Risk.LOW`: Read operations (`catalog.get_product`, `orders.get`).
- `Risk.MEDIUM`: Stateful non-destructive mutations (`inventory.reserve`).
- `Risk.HIGH`: Financial mutations (`payments.authorize`, `orders.create`).
- `Risk.CRITICAL`: Destructive actions (`orders.cancel`).

Runtime policies implement `agnara.policy.Policy.evaluate(context)` to verify caller scopes and business invariants before handler execution.

### Layer 6: Execution Runtime
Invocations pass through `invoke_result(plan, context)`. The runtime binds dependencies, checks monotonic deadlines, and manages task execution.

### Layer 7: Canonical Outcomes & Error Discipline
Instead of arbitrary exceptions bubbling to callers, operations return `CanonicalResult[T]`:
- `Success(value)`: The operation completed successfully.
- `Failure(code, message, details)`: The operation failed with a semantic `FailureCode`. Details are protected using read-only `MappingProxyType`.

### Layer 8: Observability
Telemetry hooks (`TelemetryHook`) observe `InvocationStartEvent` and `InvocationTerminalEvent`. Observers pair events via UUID4 `invocation_id` and report nanosecond latencies (`duration_ns`). Sensitive data (e.g. payment tokens) is strictly redacted.
