"""Agnara capability definitions for catalog, inventory, payments, and orders.

Declares the 6 core business operations under Agnara 0.1.0a3:
1. catalog.get_product
2. inventory.reserve
3. payments.authorize
4. orders.create
5. orders.get
6. orders.cancel

EDUCATIONAL DISCLAIMER:
payments.authorize is an explicit in-memory simulation. No real money is moved,
no payment provider or banking network is contacted, and no real credentials or card data
are accepted.
"""

from __future__ import annotations

import asyncio
import time
import uuid
from collections.abc import Callable, Iterable
from typing import Any

from agnara import (
    Agnara,
    CapabilityDefinition,
    CapabilityId,
    Confirmation,
    Idempotency,
    Policy,
    Risk,
    ScopePolicy,
    StandardEffect,
)
from agnara.execution.context import ExecutionContext
from agnara.execution.result import CanonicalResult, Failure, FailureCode, Success

from domain import (
    InventoryReservation,
    OrderCancellationResult,
    OrderItem,
    OrderRecord,
    OrderStatus,
    PaymentAuthorization,
    Product,
)
from policies import OrderCancellationPolicy, PaymentSpendingLimitPolicy
from services import (
    AuditLogger,
    CatalogRepository,
    InventoryService,
    OrderRepository,
    OutOfStockError,
    PaymentDeclineError,
    PaymentGateway,
)

__all__ = [
    "authorize_payment",
    "cancel_order",
    "catalog_app",
    "create_order",
    "get_order",
    "get_product",
    "inventory_app",
    "orders_app",
    "payments_app",
    "register_capability",
    "reserve_inventory",
]

# -----------------------------------------------------------------------------
# 1. Authoring Composition Roots (Namespaces)
# -----------------------------------------------------------------------------

catalog_app = Agnara("catalog")
inventory_app = Agnara("inventory")
payments_app = Agnara("payments")
orders_app = Agnara("orders")


def register_capability[F: Callable[..., Any]](
    app: Agnara,
    func: F,
    *,
    name: str | None = None,
    description: str | None = None,
    scopes: Iterable[str] = (),
    effects: Iterable[str] = (),
    risk: Risk | str = Risk.LOW,
    confirmation: Confirmation | str = Confirmation.NEVER,
    idempotent: bool | None = None,
    policies: Iterable[Policy] = (),
) -> F:
    """Register a capability with metadata, effects, risk, and runtime policies.

    In Agnara 0.1.0a3, `@app.capability` records metadata but does not accept
    a `policies` argument; `CapabilityDefinition.declare` accepts `policies`.
    This helper bridges declarative metadata with runtime policy binding.
    """
    cap_name = name if name is not None else getattr(func, "__name__", "")
    cap_id = CapabilityId(namespace=app.name, name=cap_name)

    idempotency_state = (
        Idempotency.UNKNOWN
        if idempotent is None
        else (Idempotency.YES if idempotent else Idempotency.NO)
    )

    definition = CapabilityDefinition.declare(
        id=cap_id,
        handler=func,
        description=description or func.__doc__,
        scopes=scopes,
        effects=effects,
        risk=risk,
        confirmation=confirmation,
        idempotency=idempotency_state,
        policies=policies,
    )
    app.capabilities.register(definition)
    return func


# -----------------------------------------------------------------------------
# 2. Capability: catalog.get_product
# -----------------------------------------------------------------------------


def get_product(
    sku: str,
    catalog: CatalogRepository,
) -> CanonicalResult[Product]:
    """Retrieve product details from the catalog by SKU."""
    product = catalog.get_product(sku)
    if product is None:
        return Failure(
            FailureCode.NOT_FOUND,
            f"product with SKU '{sku}' not found",
            details={"sku": sku},
        )
    return Success(product)


register_capability(
    catalog_app,
    get_product,
    name="get_product",
    description="Retrieve product specification and stock level by SKU.",
    scopes=["catalog:read"],
    effects=[StandardEffect.READ],
    risk=Risk.LOW,
    idempotent=True,
    policies=[ScopePolicy(["catalog:read"])],
)


# -----------------------------------------------------------------------------
# 3. Capability: inventory.reserve
# -----------------------------------------------------------------------------


def reserve_inventory(
    order_id: str,
    items: list[dict[str, Any]],
    inventory: InventoryService,
    ctx: ExecutionContext,
) -> CanonicalResult[InventoryReservation]:
    """Atomically reserve inventory stock for an order."""
    parsed_items: list[OrderItem] = []
    for raw in items:
        sku = raw.get("sku")
        qty = raw.get("quantity")
        unit_price = raw.get("unit_price_cents", 0)
        if not isinstance(sku, str) or not isinstance(qty, int) or qty <= 0:
            return Failure(
                FailureCode.INVALID_INPUT,
                f"invalid reservation item: {raw}",
                details={"item": raw},
            )
        parsed_items.append(OrderItem(sku=sku, quantity=qty, unit_price_cents=int(unit_price)))

    try:
        reservation = inventory.reserve(order_id, parsed_items)
        return Success(reservation)
    except OutOfStockError as err:
        return Failure(
            FailureCode.CONFLICT,
            str(err),
            details={
                "order_id": order_id,
                "sku": err.sku,
                "requested": err.requested,
                "available": err.available,
            },
        )


register_capability(
    inventory_app,
    reserve_inventory,
    name="reserve",
    description="Reserve warehouse stock for pending order items.",
    scopes=["inventory:write"],
    effects=[StandardEffect.DATABASE_WRITE],
    risk=Risk.MEDIUM,
    idempotent=False,
    policies=[ScopePolicy(["inventory:write"])],
)


# -----------------------------------------------------------------------------
# 4. Capability: payments.authorize
# -----------------------------------------------------------------------------


def authorize_payment(
    payment_id: str,
    order_id: str,
    customer_id: str,
    amount_cents: int,
    payment_ref: str,
    gateway: PaymentGateway,
    ctx: ExecutionContext,
) -> CanonicalResult[PaymentAuthorization]:
    """Simulate payment fund authorization with spending limit check.

    EDUCATIONAL DISCLAIMER:
    No money is moved. No payment processor is contacted.
    This capability exists only to demonstrate a sensitive operation contract
    and policy guardrail behavior.
    """
    try:
        auth = gateway.authorize(
            payment_id=payment_id,
            order_id=order_id,
            customer_id=customer_id,
            amount_cents=amount_cents,
            payment_ref=payment_ref,
        )
        return Success(auth)
    except PaymentDeclineError as err:
        return Failure(
            FailureCode.FORBIDDEN,
            str(err),
            details=err.details,
        )


register_capability(
    payments_app,
    authorize_payment,
    name="authorize",
    description="Authorize credit or payment reference for an order amount.",
    scopes=["payments:write"],
    effects=[StandardEffect.FINANCIAL_WRITE],
    risk=Risk.HIGH,
    idempotent=False,
    policies=[
        ScopePolicy(["payments:write"]),
        PaymentSpendingLimitPolicy(max_amount_cents=500_000),
    ],
)


# -----------------------------------------------------------------------------
# 5. Capability: orders.create
# -----------------------------------------------------------------------------


async def create_order(
    order_id: str,
    customer_id: str,
    items: list[dict[str, Any]],
    payment_ref: str,
    catalog: CatalogRepository,
    inventory: InventoryService,
    gateway: PaymentGateway,
    orders: OrderRepository,
    audit: AuditLogger,
    ctx: ExecutionContext,
) -> CanonicalResult[OrderRecord]:
    """Orchestrate end-to-end order validation, reservation, payment, and persistence."""
    # 1. Validate items against catalog
    if not items:
        return Failure(
            FailureCode.INVALID_INPUT,
            "order items list cannot be empty",
            details={"order_id": order_id},
        )

    parsed_items: list[OrderItem] = []
    for raw in items:
        sku = raw.get("sku")
        qty = raw.get("quantity")
        if not isinstance(sku, str) or not isinstance(qty, int) or qty <= 0:
            return Failure(
                FailureCode.INVALID_INPUT,
                f"invalid item specification: {raw}",
                details={"order_id": order_id, "item": raw},
            )
        product = catalog.get_product(sku)
        if product is None:
            return Failure(
                FailureCode.NOT_FOUND,
                f"catalog product '{sku}' does not exist",
                details={"order_id": order_id, "sku": sku},
            )
        parsed_items.append(
            OrderItem(
                sku=sku,
                quantity=qty,
                unit_price_cents=product.unit_price_cents,
            )
        )

    total_cents = sum(item.total_cents for item in parsed_items)

    # 2. Reserve inventory
    try:
        reservation = inventory.reserve(order_id, parsed_items)
    except OutOfStockError as err:
        audit.record(
            ctx.tracking_id,
            "orders.create",
            f"Order reservation failed: {err}",
            order_id=order_id,
            sku=err.sku,
        )
        return Failure(
            FailureCode.CONFLICT,
            str(err),
            details={
                "order_id": order_id,
                "sku": err.sku,
                "requested": err.requested,
                "available": err.available,
            },
        )

    # Cooperative async dispatch point (simulates external network / persistence latency)
    await asyncio.sleep(0.001)

    # 3. Authorize payment (simulated)
    payment_id = f"pay_{uuid.uuid4().hex[:10]}"
    try:
        auth = gateway.authorize(
            payment_id=payment_id,
            order_id=order_id,
            customer_id=customer_id,
            amount_cents=total_cents,
            payment_ref=payment_ref,
        )
    except PaymentDeclineError as err:
        # Roll back inventory reservation on payment decline
        inventory.release(reservation.reservation_id)
        audit.record(
            ctx.tracking_id,
            "orders.create",
            "Payment declined; released reserved inventory",
            order_id=order_id,
            reservation_id=reservation.reservation_id,
        )
        return Failure(
            FailureCode.FORBIDDEN,
            str(err),
            details={"order_id": order_id, "amount_cents": total_cents},
        )

    # 4. Persist confirmed order
    order = OrderRecord(
        order_id=order_id,
        customer_id=customer_id,
        items=tuple(parsed_items),
        total_cents=total_cents,
        status=OrderStatus.CONFIRMED,
        reservation_id=reservation.reservation_id,
        authorization_id=auth.authorization_id,
        created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        tracking_id=ctx.tracking_id,
    )
    orders.save(order)
    audit.record(
        ctx.tracking_id,
        "orders.create",
        "Order created and confirmed successfully",
        order_id=order_id,
        total_cents=total_cents,
        reservation_id=reservation.reservation_id,
        authorization_id=auth.authorization_id,
    )
    return Success(order)


register_capability(
    orders_app,
    create_order,
    name="create",
    description="Validate order, reserve inventory, authorize payment, and persist order.",
    scopes=["orders:write"],
    effects=[StandardEffect.DATABASE_WRITE, StandardEffect.FINANCIAL_WRITE],
    risk=Risk.HIGH,
    idempotent=False,
    policies=[
        ScopePolicy(["orders:write"]),
        PaymentSpendingLimitPolicy(max_amount_cents=500_000),
    ],
)


# -----------------------------------------------------------------------------
# 6. Capability: orders.get
# -----------------------------------------------------------------------------


def get_order(
    order_id: str,
    orders: OrderRepository,
) -> CanonicalResult[OrderRecord]:
    """Retrieve an existing customer order record by order identifier."""
    order = orders.get(order_id)
    if order is None:
        return Failure(
            FailureCode.NOT_FOUND,
            f"order '{order_id}' not found",
            details={"order_id": order_id},
        )
    return Success(order)


register_capability(
    orders_app,
    get_order,
    name="get",
    description="Retrieve order record by order_id.",
    scopes=["orders:read"],
    effects=[StandardEffect.READ],
    risk=Risk.LOW,
    idempotent=True,
    policies=[ScopePolicy(["orders:read"])],
)


# -----------------------------------------------------------------------------
# 7. Capability: orders.cancel
# -----------------------------------------------------------------------------


async def cancel_order(
    order_id: str,
    reason: str,
    orders: OrderRepository,
    inventory: InventoryService,
    gateway: PaymentGateway,
    audit: AuditLogger,
    ctx: ExecutionContext,
) -> CanonicalResult[OrderCancellationResult]:
    """Cancel an active order, releasing inventory and voiding payment authorization."""
    order = orders.get(order_id)
    if order is None:
        return Failure(
            FailureCode.NOT_FOUND,
            f"order '{order_id}' not found",
            details={"order_id": order_id},
        )

    if order.status == OrderStatus.CANCELLED:
        # Idempotent response
        return Success(
            OrderCancellationResult(
                order_id=order.order_id,
                status=OrderStatus.CANCELLED,
                reason=reason,
                released_reservation_id=order.reservation_id,
                voided_authorization_id=order.authorization_id,
            )
        )

    # 1. Release inventory
    released_res_id = None
    if order.reservation_id is not None:
        inventory.release(order.reservation_id)
        released_res_id = order.reservation_id

    # 2. Void payment authorization
    voided_auth_id = None
    if order.authorization_id is not None:
        gateway.void_authorization(order.authorization_id)
        voided_auth_id = order.authorization_id

    # Cooperative async dispatch point
    await asyncio.sleep(0.001)

    # 3. Update order record
    orders.update_status(order_id, OrderStatus.CANCELLED)
    audit.record(
        ctx.tracking_id,
        "orders.cancel",
        f"Order cancelled: {reason}",
        order_id=order_id,
        released_reservation_id=released_res_id,
        voided_authorization_id=voided_auth_id,
    )

    return Success(
        OrderCancellationResult(
            order_id=order_id,
            status=OrderStatus.CANCELLED,
            reason=reason,
            released_reservation_id=released_res_id,
            voided_authorization_id=voided_auth_id,
        )
    )


register_capability(
    orders_app,
    cancel_order,
    name="cancel",
    description="Cancel order, releasing stock and voiding payment authorizations.",
    scopes=["orders:cancel"],
    effects=[
        StandardEffect.DATABASE_WRITE,
        StandardEffect.FINANCIAL_WRITE,
        StandardEffect.DESTRUCTIVE,
    ],
    risk=Risk.CRITICAL,
    idempotent=True,
    policies=[
        ScopePolicy(["orders:cancel"]),
        OrderCancellationPolicy(min_reason_length=5),
    ],
)
