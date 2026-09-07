"""Tests for policy guardrails, risk metadata, and scope enforcement."""

from __future__ import annotations

import asyncio

from agnara.capability import Idempotency, Risk, StandardEffect
from agnara.execution.result import Failure, FailureCode, Success
from agnara.policy import Principal

from service import ReferenceOrderService


def test_scope_policy_denial() -> None:
    """Invoking a capability without required scopes is denied with FailureCode.FORBIDDEN."""

    async def _run() -> None:
        service = ReferenceOrderService()

        # Principal has only read scopes
        reader = Principal(identity="reader-user", scopes=["catalog:read", "orders:read"])

        # Attempt to invoke orders.create which requires 'orders:write'
        res = await service.create_order(
            order_id="ORD-NO-SCOPE",
            customer_id="CUST-42",
            items=[{"sku": "SKU-KEYBOARD-02", "quantity": 1}],
            payment_ref="sim-ref-standard-99",
            principal=reader,
        )
        assert isinstance(res, Failure)
        assert res.code == FailureCode.FORBIDDEN
        assert "missing required scopes: orders:write" in res.message

    asyncio.run(_run())


def test_spending_limit_policy_enforcement() -> None:
    """PaymentSpendingLimitPolicy rejects transactions above $5,000 without override scope."""

    async def _run() -> None:
        service = ReferenceOrderService()

        standard_user = Principal(
            identity="standard-user",
            scopes=["catalog:read", "orders:write", "payments:write"],
        )

        # SKU-SERVER-05 costs $7,500.00 (750,000 cents) > $5,000.00
        res = await service.create_order(
            order_id="ORD-EXPENSIVE",
            customer_id="CUST-42",
            items=[{"sku": "SKU-SERVER-05", "quantity": 1}],
            payment_ref="sim-ref-standard-99",
            principal=standard_user,
        )
        assert isinstance(res, Failure)
        assert res.code == FailureCode.FORBIDDEN
        assert "exceeds spending limit of 500000 cents" in res.message

        # Principal with 'payments:unlimited' bypasses the spending limit
        privileged_user = Principal(
            identity="vip-buyer",
            scopes=["catalog:read", "orders:write", "payments:write", "payments:unlimited"],
        )
        res_bypass = await service.create_order(
            order_id="ORD-EXPENSIVE-ALLOWED",
            customer_id="CUST-42",
            items=[{"sku": "SKU-SERVER-05", "quantity": 1}],
            payment_ref="sim-ref-corporate-42",
            principal=privileged_user,
        )
        assert isinstance(res_bypass, Success)
        assert res_bypass.value.order_id == "ORD-EXPENSIVE-ALLOWED"

    asyncio.run(_run())


def test_order_cancellation_policy_reason_guardrail() -> None:
    """OrderCancellationPolicy requires a substantive cancellation reason (>= 5 chars)."""

    async def _run() -> None:
        service = ReferenceOrderService()

        operator = Principal(
            identity="operator",
            scopes=["orders:cancel", "orders:write", "catalog:read"],
        )

        # Too short reason (< 5 characters)
        res = await service.cancel_order(
            order_id="ORD-ANY",
            reason="no",
            principal=operator,
        )
        assert isinstance(res, Failure)
        assert res.code == FailureCode.FORBIDDEN
        assert "cancellation reason must be at least 5 characters" in res.message

    asyncio.run(_run())


def test_capability_metadata_attributes() -> None:
    """Compiled capability plans preserve accurate operational metadata."""
    service = ReferenceOrderService()

    for pid, plan in service.plans.items():
        if pid.name == "get_product":
            assert plan.definition.risk == Risk.LOW
            assert StandardEffect.READ in plan.definition.effects
            assert plan.definition.idempotency == Idempotency.YES
        elif pid.name == "cancel":
            assert plan.definition.risk == Risk.CRITICAL
            assert StandardEffect.DESTRUCTIVE in plan.definition.effects
            assert plan.definition.idempotency == Idempotency.YES
        elif pid.name == "create":
            assert plan.definition.risk == Risk.HIGH
            assert StandardEffect.DATABASE_WRITE in plan.definition.effects
            assert plan.definition.idempotency == Idempotency.NO
