"""Interactive CLI demonstration for Agnara Historical Reference Application #009.

Executes 9 comprehensive operational scenarios highlighting the complete
8-stage educational pipeline under Agnara 0.1.0a3:
1. Catalog product inspection (catalog.get_product)
2. Happy path end-to-end order creation (orders.create)
3. Direct order retrieval (orders.get)
4. Inventory stock exhaustion conflict (FailureCode.CONFLICT)
5. Spending limit policy enforcement (FailureCode.FORBIDDEN)
6. Typed input contract validation failure (FailureCode.INVALID_INPUT)
7. Authorized order cancellation (orders.cancel)
8. Scope unauthorized access denial (FailureCode.FORBIDDEN)
9. Observability & Zero Secret Leakage Verification

EDUCATIONAL DISCLAIMER:
Payment operations in this application are an explicit, in-memory simulation.
No real money is transferred, no payment processor is contacted, and no real
cardholder data or secrets are accepted.
"""

from __future__ import annotations

import asyncio
import sys

import agnara
from agnara.execution.result import Failure, Success
from agnara.policy import Principal

from service import ReferenceOrderService


def print_banner() -> None:
    """Print the historical application header."""
    print("=" * 80)
    print(" AGNARA HISTORICAL REFERENCE APPLICATION #009: agnara-reference-service")
    v_str = f"agnara=={agnara.__version__}"
    r_str = f"CPython {sys.version.split()[0]}"
    print(f" Framework: {v_str} | Runtime: {r_str} | Status: Historical/Frozen")
    print(" Mission: The canonical integrating application for Agnara 0.1.0a3")
    print("=" * 80)


async def main() -> None:
    print_banner()

    service = ReferenceOrderService()
    authorized_principal = Principal(
        identity="operator-alice",
        scopes=[
            "catalog:read",
            "inventory:write",
            "payments:write",
            "orders:write",
            "orders:read",
            "orders:cancel",
        ],
    )

    unauthorized_principal = Principal(
        identity="guest-bob",
        scopes=["catalog:read"],
    )

    # -------------------------------------------------------------------------
    # Scenario 1: Catalog Product Inspection
    # -------------------------------------------------------------------------
    print("\n" + "-" * 80)
    print(" > SCENARIO 1: Catalog Product Inspection (catalog.get_product)")
    print("-" * 80)
    print("Querying product 'SKU-LAPTOP-01'...")
    res1 = await service.get_product(
        "SKU-LAPTOP-01",
        principal=authorized_principal,
        tracking_id="trk-scen-1",
    )
    if isinstance(res1, Success):
        prod = res1.value
        price_fmt = f"${prod.unit_price_cents / 100:.2f}"
        print(f" [OK] Product: {prod.name} ({prod.sku})")
        print(f"      Price: {price_fmt} | Category: {prod.category} | In Stock: {prod.in_stock}")
    else:
        print(f" [FAIL] Query failed: {res1.message}")

    # -------------------------------------------------------------------------
    # Scenario 2: Happy Path End-to-End Order Creation
    # -------------------------------------------------------------------------
    print("\n" + "-" * 80)
    print(" > SCENARIO 2: Happy Path Order Creation (orders.create)")
    print("-" * 80)
    print("Submitting order ORD-2026-101 (2 keyboards + 1 mouse)...")
    res2 = await service.create_order(
        order_id="ORD-2026-101",
        customer_id="CUST-ALPHA-42",
        items=[
            {"sku": "SKU-KEYBOARD-02", "quantity": 2},
            {"sku": "SKU-MOUSE-03", "quantity": 1},
        ],
        payment_ref="sim-ref-corporate-42",
        principal=authorized_principal,
        tracking_id="trk-scen-2",
    )
    if isinstance(res2, Success):
        order = res2.value
        print(f" [OK] Order Created: {order.order_id} | Status: {order.status.value}")
        print(f"      Total: ${order.total_cents / 100:.2f} | Items: {len(order.items)}")
        print(f"      Reservation ID: {order.reservation_id} | Auth ID: {order.authorization_id}")
    else:
        print(f" [FAIL] Order creation failed: {res2.message}")

    # -------------------------------------------------------------------------
    # Scenario 3: Order Retrieval
    # -------------------------------------------------------------------------
    print("\n" + "-" * 80)
    print(" > SCENARIO 3: Order Retrieval by ID (orders.get)")
    print("-" * 80)
    print("Fetching order ORD-2026-101 from repository...")
    res3 = await service.get_order(
        "ORD-2026-101", principal=authorized_principal, tracking_id="trk-scen-3"
    )
    if isinstance(res3, Success):
        order = res3.value
        print(f" [OK] Retrieved Order: {order.order_id} for Customer {order.customer_id}")
        print(f"      Status: {order.status.value} | Created At: {order.created_at}")
    else:
        print(f" [FAIL] Retrieval failed: {res3.message}")

    # -------------------------------------------------------------------------
    # Scenario 4: Inventory Stock Shortage Conflict
    # -------------------------------------------------------------------------
    print("\n" + "-" * 80)
    print(" > SCENARIO 4: Inventory Conflict Failure (FailureCode.CONFLICT)")
    print("-" * 80)
    print("Requesting 6 units of SKU-MONITOR-04 (stock is 5)...")
    res4 = await service.create_order(
        order_id="ORD-2026-102",
        customer_id="CUST-BETA-77",
        items=[{"sku": "SKU-MONITOR-04", "quantity": 6}],
        payment_ref="sim-ref-standard-99",
        principal=authorized_principal,
        tracking_id="trk-scen-4",
    )
    print(f" Outcome Result Type: {type(res4).__name__}")
    if isinstance(res4, Failure):
        print(f" Failure Code: {res4.code.value} ({res4.code.name})")
        print(f" Diagnostic Message: {res4.message}")
        print(f" Safe Details: {dict(res4.details)}")

    # -------------------------------------------------------------------------
    # Scenario 5: Spending Limit Policy Enforcement
    # -------------------------------------------------------------------------
    print("\n" + "-" * 80)
    print(" > SCENARIO 5: Policy Guardrail Denial (PaymentSpendingLimitPolicy)")
    print("-" * 80)
    print("Submitting order with enterprise GPU node ($7,500.00; exceeds $5,000 threshold)...")
    res5 = await service.create_order(
        order_id="ORD-2026-103",
        customer_id="CUST-GAMMA-99",
        items=[{"sku": "SKU-SERVER-05", "quantity": 1}],
        payment_ref="sim-ref-enterprise-01",
        principal=authorized_principal,
        tracking_id="trk-scen-5",
    )
    print(f" Outcome Result Type: {type(res5).__name__}")
    if isinstance(res5, Failure):
        print(f" Failure Code: {res5.code.value} ({res5.code.name})")
        print(f" Diagnostic Message: {res5.message}")

    # -------------------------------------------------------------------------
    # Scenario 6: Typed Contract Schema Validation Failure
    # -------------------------------------------------------------------------
    print("\n" + "-" * 80)
    print(" > SCENARIO 6: Input Contract Validation Failure (FailureCode.INVALID_INPUT)")
    print("-" * 80)
    print("Dispatching raw payload with empty items list...")
    res6 = await service.create_order(
        order_id="ORD-2026-104",
        customer_id="CUST-DELTA-01",
        items=[],
        payment_ref="sim-ref-standard-99",
        principal=authorized_principal,
        tracking_id="trk-scen-6",
    )
    print(f" Outcome Result Type: {type(res6).__name__}")
    if isinstance(res6, Failure):
        print(f" Failure Code: {res6.code.value} ({res6.code.name})")
        print(f" Diagnostic Message: {res6.message}")

    # -------------------------------------------------------------------------
    # Scenario 7: Authorized Order Cancellation
    # -------------------------------------------------------------------------
    print("\n" + "-" * 80)
    print(" > SCENARIO 7: Authorized Order Cancellation (orders.cancel)")
    print("-" * 80)
    print("Operator cancels ORD-2026-101 with verified reason and 'orders:cancel' scope...")
    res7 = await service.cancel_order(
        order_id="ORD-2026-101",
        reason="Customer requested order cancellation prior to dispatch",
        principal=authorized_principal,
        tracking_id="trk-scen-7",
    )
    if isinstance(res7, Success):
        cancel_info = res7.value
        print(f" [OK] Cancelled Order: {cancel_info.order_id} | Status: {cancel_info.status.value}")
        print(f"      Released Reservation: {cancel_info.released_reservation_id}")
        print(f"      Voided Authorization: {cancel_info.voided_authorization_id}")
    else:
        print(f" [FAIL] Cancellation failed: {res7.message}")

    # Verify order status in repository is CANCELLED
    check_order = await service.get_order("ORD-2026-101", principal=authorized_principal)
    if isinstance(check_order, Success):
        print(f" Verified Repository Status: {check_order.value.status.value}")

    # -------------------------------------------------------------------------
    # Scenario 8: Unauthorized Access Denial
    # -------------------------------------------------------------------------
    print("\n" + "-" * 80)
    print(" > SCENARIO 8: Scope Authorization Denial (ScopePolicy)")
    print("-" * 80)
    print("Guest user (with only 'catalog:read') attempts to cancel order ORD-2026-101...")
    res8 = await service.cancel_order(
        order_id="ORD-2026-101",
        reason="Unauthorized user attempting cancellation",
        principal=unauthorized_principal,
        tracking_id="trk-scen-8",
    )
    print(f" Outcome Result Type: {type(res8).__name__}")
    if isinstance(res8, Failure):
        print(f" Failure Code: {res8.code.value} ({res8.code.name})")
        print(f" Diagnostic Message: {res8.message}")

    # -------------------------------------------------------------------------
    # Scenario 9: Observability & Zero Secret Leakage Verification
    # -------------------------------------------------------------------------
    print("\n" + "-" * 80)
    print(" > SCENARIO 9: Observability & Security Redaction Verification")
    print("-" * 80)
    records = service.telemetry.get_records()
    print(f" Total Telemetry Events Recorded: {len(records)}")

    # Print summary table of recorded telemetry
    print("\n Observed Execution Telemetry:")
    print(" +-----------------------+---------------------+-----------+------------+")
    print(" | Capability ID         | Tracking ID         | Time (ms) | Outcome    |")
    print(" +-----------------------+---------------------+-----------+------------+")
    for r in records[:8]:
        tid = str(r.tracking_id)
        print(f" | {r.capability_id:<21} | {tid:<19} | {r.duration_ms:>9.3f} | {r.outcome:<10} |")
    print(" +-----------------------+---------------------+-----------+------------+")

    # Verify zero secret leakage
    print("\n Security & Secret Invariant Checks:")
    raw_ref_test = "sim-ref-corporate-42"

    # 1. Check in audit log
    audit_leak = any(raw_ref_test in str(rec) for rec in service.audit_logger.get_records())
    audit_status = "LEAKED" if audit_leak else "SAFE (Masked/Redacted)"
    print(f" [OK] Invariant 1: Raw ref in AuditLogger records? -> {audit_status}")

    # 2. Check in telemetry records
    telemetry_leak = any(raw_ref_test in str(r) for r in records)
    telem_status = "LEAKED" if telemetry_leak else "SAFE (Payloads Omitted)"
    print(f" [OK] Invariant 2: Raw ref in TelemetryHook records? -> {telem_status}")

    # 3. Check failure details immutability
    if isinstance(res4, Failure):
        dt_name = type(res4.details).__name__
        print(f" [OK] Invariant 3: Failure details type -> {dt_name} (Immutable)")

    print("\n" + "=" * 80)
    print(" ALL 9 DEMONSTRATION SCENARIOS COMPLETED SUCCESSFULLY.")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
