---
name: documentation
description: Standards and synchronization rules for maintaining agnara-reference-service (#009) documentation.
---

# Documentation Skill

Use this skill when reading, authoring, or updating documentation in **Agnara Historical Reference Application #009 (`agnara-reference-service`)**.

---

## 1. When to Use This Skill

Activate this skill whenever:
- Updating or auditing `README.md`, `ARCHITECTURE.md`, `AGENTS.md`, or `docs/`.
- Documenting the 8-layer educational execution pipeline.
- Maintaining the verified public API surface audit in `docs/public-api-boundary.md`.
- Documenting the clean 3-tier boundary: Agnara Framework vs Application Service vs Infrastructure Simulators.
- Maintaining historical release ledger in `CHANGELOG.md` and contribution rules in `CONTRIBUTING.md`.

---

## 2. Relevant Inputs

- **`README.md`:** Comprehensive pedagogical guide, capability matrix, reproducible commands, and educational walkthrough.
- **`ARCHITECTURE.md`:** System architecture, 3-tier boundaries, 8-layer execution pipeline, and ADR alignments.
- **`AGENTS.md`:** Single source of operational truth for AI coding agents.
- **`docs/public-api-boundary.md`:** Verified public API surface vs discarded speculative ideas.
- **`docs/architecture-guide.md`:** Deep-dive guide into the 8-layer educational pipeline.
- **`CHANGELOG.md`:** Historical release ledger following Keep a Changelog.
- **`CONTRIBUTING.md`:** Contribution rules under Historical / Frozen status.
- **`SECURITY.md`:** Security policy, secret redaction, and vulnerability reporting.

---

## 3. Ordered Implementation Workflow

### Step 1: Architectural Boundary Verification
Verify that documentation strictly adheres to the 3-tier separation:
1. **Tier 1: Agnara 0.1.0a3 Core:** Capability definitions, plan compilation, DI resolution, policies, execution runtime, telemetry hooks.
2. **Tier 2: Application Domain & Service:** ReferenceOrderService, domain entities, business policies.
3. **Tier 3: In-Memory Infrastructure:** Catalog, inventory, simulated payment gateway, order store, audit logger.

### Step 2: Educational Pipeline Synchronization
Ensure all docs clearly delineate the 8 pipeline layers and map them to the 5 foundational reference apps (#004–#008).

### Step 3: Baseline & Fictional Payment Disclaimers
1. Ensure `agnara==0.1.0a3` and CPython >= 3.14 are visibly pinned.
2. Confirm the Historical / Frozen badge and status are prominent.
3. Confirm clear disclaimers that payment simulations do not handle real money, banking cards, or PANs.

---

## 4. Operational Boundaries & Negative Constraints

- **No Speculative APIs:** Never describe features from later Agnara versions as present in `0.1.0a3`.
- **No Placeholder Content:** Never leave `TODO`, `TBD`, or temporary comments in documentation.
- **Clean UTF-8:** All documentation files must be saved as UTF-8 without Byte Order Marks (BOM).

---

## 5. Validations & Definition of Done

The documentation workflow is complete when:
- [ ] All architectural guides and public boundary audits match executable code.
- [ ] All file links and symbol references are accurate.
- [ ] Markdown formatting passes validation without warnings.
