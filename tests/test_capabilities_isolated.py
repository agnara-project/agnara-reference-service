"""Tests for isolated capabilities behavior and error handling."""

from __future__ import annotations

import asyncio

from agnara.execution.result import Failure, FailureCode, Success

from capabilities import (
    authorize_payment,
    cancel_order,
    create_order,
    get_product,
    reserve_inventory,
)
from domain import (
    InventoryReservation,
    OrderCancellationResult,
    OrderStatus,
    PaymentAuthorization,
    Product,
    ReservationStatus,
)
from services import (
    AuditLogger,
    CatalogRepository,
    InventoryService,
    OrderRepository,
    PaymentGateway,
)


class MockContext:
    """Minimal context simulation for isolated handler testing."""

    def __init__(self, tracking_id: str = "trk-unit") -> None:
        self.tracking_id = tracking_id


def test_catalog_get_product_success() -> None:
    """catalog.get_product returns product details for existing SKU."""
    catalog = CatalogRepository()
    result = get_product("SKU-LAPTOP-01", catalog)
    assert isinstance(result, Success)
    assert isinstance(result.value, Product)
    assert result.value.sku == "SKU-LAPTOP-01"
    assert result.value.unit_price_cents == 199900


def test_catalog_get_product_not_found() -> None:
    """catalog.get_product returns FailureCode.NOT_FOUND for unknown SKU."""
    catalog = CatalogRepository()
    result = get_product("SKU-UNKNOWN", catalog)
    assert isinstance(result, Failure)
    assert result.code == FailureCode.NOT_FOUND
    assert "not found" in result.message


def test_inventory_reserve_success() -> None:
    """inventory.reserve successfully allocates stock."""
    catalog = CatalogRepository()
    inventory = InventoryService(catalog)
    ctx = MockContext()

    result = reserve_inventory(
        order_id="ORD-T1",
        items=[{"sku": "SKU-KEYBOARD-02", "quantity": 5}],
        inventory=inventory,
        ctx=ctx,  # type: ignore[arg-type]
    )
    assert isinstance(result, Success)
    assert isinstance(result.value, InventoryReservation)
    assert result.value.status == ReservationStatus.RESERVED
    assert inventory.get_stock("SKU-KEYBOARD-02") == 45


def test_inventory_reserve_conflict_out_of_stock() -> None:
    """inventory.reserve returns FailureCode.CONFLICT when stock is depleted."""
    catalog = CatalogRepository()
    inventory = InventoryService(catalog)
    ctx = MockContext()

    result = reserve_inventory(
        order_id="ORD-T2",
        items=[{"sku": "SKU-MONITOR-04", "quantity": 99}],
        inventory=inventory,
        ctx=ctx,  # type: ignore[arg-type]
    )
    assert isinstance(result, Failure)
    assert result.code == FailureCode.CONFLICT
    assert result.details["available"] == 5
    assert result.details["requested"] == 99


def test_payments_authorize_success() -> None:
    """payments.authorize returns authorized status for valid test reference."""
    gateway = PaymentGateway()
    ctx = MockContext()

    result = authorize_payment(
        payment_id="pay_001",
        order_id="ORD-T3",
        customer_id="CUST-1",
        amount_cents=15000,
        payment_ref="sim-ref-valid-1234",
        gateway=gateway,
        ctx=ctx,  # type: ignore[arg-type]
    )
    assert isinstance(result, Success)
    assert isinstance(result.value, PaymentAuthorization)
    assert result.value.sanitized_ref == "sim-***1234"


def test_payments_authorize_decline() -> None:
    """payments.authorize returns FailureCode.FORBIDDEN when declined."""
    gateway = PaymentGateway()
    ctx = MockContext()

    result = authorize_payment(
        payment_id="pay_002",
        order_id="ORD-T4",
        customer_id="CUST-1",
        amount_cents=15000,
        payment_ref="sim-ref-declined",
        gateway=gateway,
        ctx=ctx,  # type: ignore[arg-type]
    )
    assert isinstance(result, Failure)
    assert result.code == FailureCode.FORBIDDEN


def test_orders_create_success_and_rollback_on_payment_decline() -> None:
    """orders.create reserves stock, but rolls back inventory if payment declines."""

    async def _run() -> None:
        catalog = CatalogRepository()
        inventory = InventoryService(catalog)
        gateway = PaymentGateway()
        orders = OrderRepository()
        audit = AuditLogger()
        ctx = MockContext()

        initial_stock = inventory.get_stock("SKU-KEYBOARD-02")

        # Payment declined token triggers rollback
        result = await create_order(
            order_id="ORD-T5",
            customer_id="CUST-1",
            items=[{"sku": "SKU-KEYBOARD-02", "quantity": 2}],
            payment_ref="sim-ref-declined",
            catalog=catalog,
            inventory=inventory,
            gateway=gateway,
            orders=orders,
            audit=audit,
            ctx=ctx,  # type: ignore[arg-type]
        )
        assert isinstance(result, Failure)
        assert result.code == FailureCode.FORBIDDEN

        # Inventory must have been restored
        assert inventory.get_stock("SKU-KEYBOARD-02") == initial_stock

    asyncio.run(_run())


def test_orders_cancel_lifecycle_and_idempotency() -> None:
    """orders.cancel releases reservation, voids payment, and behaves idempotently."""

    async def _run() -> None:
        catalog = CatalogRepository()
        inventory = InventoryService(catalog)
        gateway = PaymentGateway()
        orders = OrderRepository()
        audit = AuditLogger()
        ctx = MockContext()

        # 1. Create order
        create_res = await create_order(
            order_id="ORD-T6",
            customer_id="CUST-1",
            items=[{"sku": "SKU-MOUSE-03", "quantity": 3}],
            payment_ref="sim-ref-valid-standard",
            catalog=catalog,
            inventory=inventory,
            gateway=gateway,
            orders=orders,
            audit=audit,
            ctx=ctx,  # type: ignore[arg-type]
        )
        assert isinstance(create_res, Success)
        assert inventory.get_stock("SKU-MOUSE-03") == 72

        # 2. Cancel order
        cancel_res = await cancel_order(
            order_id="ORD-T6",
            reason="Customer requested cancellation",
            orders=orders,
            inventory=inventory,
            gateway=gateway,
            audit=audit,
            ctx=ctx,  # type: ignore[arg-type]
        )
        assert isinstance(cancel_res, Success)
        assert isinstance(cancel_res.value, OrderCancellationResult)
        assert cancel_res.value.status == OrderStatus.CANCELLED
        assert inventory.get_stock("SKU-MOUSE-03") == 75

        # 3. Cancel again (idempotent call)
        cancel_res_2 = await cancel_order(
            order_id="ORD-T6",
            reason="Repeated cancellation request",
            orders=orders,
            inventory=inventory,
            gateway=gateway,
            audit=audit,
            ctx=ctx,  # type: ignore[arg-type]
        )
        assert isinstance(cancel_res_2, Success)
        assert cancel_res_2.value.status == OrderStatus.CANCELLED

    asyncio.run(_run())
