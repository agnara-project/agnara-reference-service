"""End-to-end integration tests using ReferenceOrderService facade."""

from __future__ import annotations

import asyncio

import pytest
from agnara.execution.result import Failure, FailureCode, Success
from agnara.policy import Principal

from domain import OrderStatus
from service import ReferenceOrderService


@pytest.fixture
def admin_principal() -> Principal:
    return Principal(
        identity="admin-operator",
        scopes=[
            "catalog:read",
            "inventory:write",
            "payments:write",
            "orders:write",
            "orders:read",
            "orders:cancel",
        ],
    )


def test_service_complete_order_lifecycle(admin_principal: Principal) -> None:
    """Full end-to-end lifecycle: catalog query -> create -> get -> cancel."""

    async def _run() -> None:
        service = ReferenceOrderService()

        # 1. Query catalog
        cat_res = await service.get_product("SKU-LAPTOP-01", principal=admin_principal)
        assert isinstance(cat_res, Success)
        assert cat_res.value.sku == "SKU-LAPTOP-01"

        # 2. Create order
        create_res = await service.create_order(
            order_id="ORD-E2E-1",
            customer_id="CUST-42",
            items=[{"sku": "SKU-LAPTOP-01", "quantity": 1}],
            payment_ref="sim-ref-standard-4242",
            principal=admin_principal,
            tracking_id="trk-e2e-1",
        )
        assert isinstance(create_res, Success)
        order = create_res.value
        assert order.order_id == "ORD-E2E-1"
        assert order.total_cents == 199900
        assert order.status == OrderStatus.CONFIRMED

        # 3. Retrieve order
        get_res = await service.get_order("ORD-E2E-1", principal=admin_principal)
        assert isinstance(get_res, Success)
        assert get_res.value.order_id == "ORD-E2E-1"

        # 4. Cancel order
        cancel_res = await service.cancel_order(
            "ORD-E2E-1",
            reason="Customer requested full cancellation",
            principal=admin_principal,
            tracking_id="trk-e2e-1-cancel",
        )
        assert isinstance(cancel_res, Success)
        assert cancel_res.value.status == OrderStatus.CANCELLED

        # 5. Verify final repository status
        check_res = await service.get_order("ORD-E2E-1", principal=admin_principal)
        assert isinstance(check_res, Success)
        assert check_res.value.status == OrderStatus.CANCELLED

    asyncio.run(_run())


def test_service_order_inventory_conflict(admin_principal: Principal) -> None:
    """Service returns FailureCode.CONFLICT when ordering more than available."""

    async def _run() -> None:
        service = ReferenceOrderService()

        res = await service.create_order(
            order_id="ORD-E2E-SHORTAGE",
            customer_id="CUST-42",
            items=[{"sku": "SKU-MONITOR-04", "quantity": 6}],  # Stock is 5; total < limit
            payment_ref="sim-ref-standard-99",
            principal=admin_principal,
        )
        assert isinstance(res, Failure)
        assert res.code == FailureCode.CONFLICT
        assert "insufficient stock" in res.message

    asyncio.run(_run())


def test_service_execution_timeout(admin_principal: Principal) -> None:
    """Service converts deadline expiration into canonical FailureCode.TIMEOUT."""

    async def _run() -> None:
        service = ReferenceOrderService()

        # Pass an impossibly tight deadline to trigger TimeoutError
        res = await service.create_order(
            order_id="ORD-TIMEOUT",
            customer_id="CUST-42",
            items=[{"sku": "SKU-MOUSE-03", "quantity": 1}],
            payment_ref="sim-ref-standard-99",
            principal=admin_principal,
            timeout=0.00000001,
        )
        assert isinstance(res, Failure)
        assert res.code == FailureCode.TIMEOUT
        assert "invocation deadline exceeded" in res.message

    asyncio.run(_run())
