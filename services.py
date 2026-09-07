"""In-memory service adapters, repositories, and dependency injection registry.

Implements decoupled domain storage and simulated gateways.
These adapters teach clean architectural boundaries without requiring
heavy database containers or external network infrastructure.

EDUCATIONAL & FICTIONAL DISCLAIMER:
The PaymentGateway implementation below is an in-memory simulation.
No real money is transferred, no bank or financial API is contacted,
and no real card numbers or tokens are accepted.
"""

from __future__ import annotations

import time
import uuid
from collections.abc import Sequence
from typing import Any

from agnara.core.di import DIRegistry, Scope, provider

from domain import (
    InventoryReservation,
    OrderItem,
    OrderRecord,
    OrderStatus,
    PaymentAuthorization,
    PaymentStatus,
    Product,
    ReservationStatus,
    mask_secret,
)

__all__ = [
    "AuditLogger",
    "CatalogRepository",
    "InventoryService",
    "OrderRepository",
    "OutOfStockError",
    "PaymentDeclineError",
    "PaymentGateway",
    "build_di_registry",
]


class OutOfStockError(Exception):
    """Raised when inventory has insufficient quantity for a requested item."""

    def __init__(self, sku: str, requested: int, available: int) -> None:
        msg = f"insufficient stock for SKU '{sku}': requested {requested}, available {available}"
        super().__init__(msg)
        self.sku = sku
        self.requested = requested
        self.available = available


class PaymentDeclineError(Exception):
    """Raised when the simulated payment processor rejects an authorization."""

    def __init__(self, reason: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(reason)
        self.details = details or {}


class CatalogRepository:
    """In-memory catalog repository pre-seeded with hardware products."""

    def __init__(self) -> None:
        self._products: dict[str, Product] = {
            "SKU-LAPTOP-01": Product(
                sku="SKU-LAPTOP-01",
                name="Developer Workstation 16-inch",
                unit_price_cents=199900,
                description="High-performance laptop with 64GB RAM",
                category="computers",
                in_stock=10,
            ),
            "SKU-KEYBOARD-02": Product(
                sku="SKU-KEYBOARD-02",
                name="Mechanical Ergonomic Keyboard",
                unit_price_cents=14900,
                description="Tactile switches, split layout",
                category="accessories",
                in_stock=50,
            ),
            "SKU-MOUSE-03": Product(
                sku="SKU-MOUSE-03",
                name="Precision Wireless Mouse",
                unit_price_cents=7900,
                description="Ergonomic optical mouse with dual connectivity",
                category="accessories",
                in_stock=75,
            ),
            "SKU-MONITOR-04": Product(
                sku="SKU-MONITOR-04",
                name="4K Ultra-Wide Curved Monitor",
                unit_price_cents=69900,
                description="34-inch HDR display with USB-C hub",
                category="displays",
                in_stock=5,
            ),
            "SKU-SERVER-05": Product(
                sku="SKU-SERVER-05",
                name="Enterprise GPU Compute Node",
                unit_price_cents=750000,
                description="Rackmount AI accelerator server",
                category="enterprise",
                in_stock=2,
            ),
        }

    def get_product(self, sku: str) -> Product | None:
        """Fetch product by SKU."""
        return self._products.get(sku)

    def list_products(self) -> list[Product]:
        """List all catalog products."""
        return list(self._products.values())


class InventoryService:
    """In-memory inventory manager with atomic stock allocation and reservation lifecycle."""

    def __init__(self, catalog: CatalogRepository) -> None:
        self._catalog = catalog
        self._stock: dict[str, int] = {p.sku: p.in_stock for p in catalog.list_products()}
        self._reservations: dict[str, InventoryReservation] = {}

    def get_stock(self, sku: str) -> int:
        """Get current unreserved stock for a SKU."""
        return self._stock.get(sku, 0)

    def reserve(self, order_id: str, items: Sequence[OrderItem]) -> InventoryReservation:
        """Atomically reserve stock for an order."""
        # 1. Check availability for all items
        for item in items:
            available = self._stock.get(item.sku, 0)
            if item.quantity > available:
                raise OutOfStockError(item.sku, item.quantity, available)

        # 2. Decrement stock
        for item in items:
            self._stock[item.sku] -= item.quantity

        # 3. Create reservation record
        res_id = f"res_{uuid.uuid4().hex[:12]}"
        reservation = InventoryReservation(
            reservation_id=res_id,
            order_id=order_id,
            items=tuple(items),
            status=ReservationStatus.RESERVED,
        )
        self._reservations[res_id] = reservation
        return reservation

    def release(self, reservation_id: str) -> InventoryReservation | None:
        """Release reserved stock back to the available inventory pool."""
        res = self._reservations.get(reservation_id)
        if res is None or res.status == ReservationStatus.RELEASED:
            return res

        for item in res.items:
            self._stock[item.sku] = self._stock.get(item.sku, 0) + item.quantity

        updated = InventoryReservation(
            reservation_id=res.reservation_id,
            order_id=res.order_id,
            items=res.items,
            status=ReservationStatus.RELEASED,
        )
        self._reservations[reservation_id] = updated
        return updated

    def get_reservation(self, reservation_id: str) -> InventoryReservation | None:
        """Retrieve reservation by identifier."""
        return self._reservations.get(reservation_id)


class PaymentGateway:
    """In-memory payment gateway simulator for demonstration purposes.

    EDUCATIONAL DISCLAIMER:
    No real money is moved. No payment processor is contacted.
    No real card or banking credentials are accepted.
    """

    def __init__(self) -> None:
        self._authorizations: dict[str, PaymentAuthorization] = {}

    def authorize(
        self,
        payment_id: str,
        order_id: str,
        customer_id: str,
        amount_cents: int,
        payment_ref: str,
    ) -> PaymentAuthorization:
        """Simulate fund authorization against a test reference."""
        if not payment_ref or payment_ref == "sim-ref-declined":
            raise PaymentDeclineError(
                "simulated payment authorization declined by issuer",
                details={"order_id": order_id, "amount_cents": amount_cents},
            )

        sanitized = mask_secret(payment_ref)
        provider_ref = f"sim_gw_{uuid.uuid4().hex[:8]}"

        auth = PaymentAuthorization(
            authorization_id=payment_id,
            order_id=order_id,
            customer_id=customer_id,
            amount_cents=amount_cents,
            status=PaymentStatus.AUTHORIZED,
            sanitized_ref=sanitized,
            provider_ref=provider_ref,
        )
        self._authorizations[payment_id] = auth
        return auth

    def void_authorization(self, authorization_id: str) -> PaymentAuthorization | None:
        """Void an existing simulated payment authorization."""
        auth = self._authorizations.get(authorization_id)
        if auth is None or auth.status == PaymentStatus.VOIDED:
            return auth

        voided = PaymentAuthorization(
            authorization_id=auth.authorization_id,
            order_id=auth.order_id,
            customer_id=auth.customer_id,
            amount_cents=auth.amount_cents,
            status=PaymentStatus.VOIDED,
            sanitized_ref=auth.sanitized_ref,
            provider_ref=auth.provider_ref,
        )
        self._authorizations[authorization_id] = voided
        return voided

    def get_authorization(self, authorization_id: str) -> PaymentAuthorization | None:
        """Retrieve simulated authorization by identifier."""
        return self._authorizations.get(authorization_id)


class OrderRepository:
    """In-memory repository for customer orders."""

    def __init__(self) -> None:
        self._orders: dict[str, OrderRecord] = {}

    def save(self, order: OrderRecord) -> None:
        """Persist or update an order."""
        self._orders[order.order_id] = order

    def get(self, order_id: str) -> OrderRecord | None:
        """Retrieve order by identifier."""
        return self._orders.get(order_id)

    def update_status(self, order_id: str, status: OrderStatus) -> OrderRecord | None:
        """Update lifecycle status of an existing order."""
        existing = self._orders.get(order_id)
        if existing is None:
            return None

        updated = OrderRecord(
            order_id=existing.order_id,
            customer_id=existing.customer_id,
            items=existing.items,
            total_cents=existing.total_cents,
            status=status,
            reservation_id=existing.reservation_id,
            authorization_id=existing.authorization_id,
            created_at=existing.created_at,
            tracking_id=existing.tracking_id,
        )
        self._orders[order_id] = updated
        return updated


class AuditLogger:
    """Safe, structured in-memory audit log for operational milestones."""

    def __init__(self) -> None:
        self._records: list[dict[str, Any]] = []

    def record(
        self,
        tracking_id: str | None,
        capability_id: str,
        message: str,
        **metadata: Any,
    ) -> None:
        """Append an audit record with timestamp and safe parameters."""
        self._records.append(
            {
                "timestamp": time.time(),
                "tracking_id": tracking_id or "untracked",
                "capability_id": capability_id,
                "message": message,
                "metadata": metadata,
            }
        )

    def get_records(self, tracking_id: str | None = None) -> list[dict[str, Any]]:
        """Fetch audit records, optionally filtered by tracking ID."""
        if tracking_id is None:
            return list(self._records)
        return [r for r in self._records if r["tracking_id"] == tracking_id]

    def clear(self) -> None:
        """Clear recorded entries."""
        self._records.clear()


def build_di_registry(
    catalog: CatalogRepository | None = None,
    inventory: InventoryService | None = None,
    payments: PaymentGateway | None = None,
    orders: OrderRepository | None = None,
    audit: AuditLogger | None = None,
) -> DIRegistry:
    """Build and configure the singleton DI registry for Agnara 0.1.0a3."""
    catalog_inst = catalog if catalog is not None else CatalogRepository()
    inventory_inst = inventory if inventory is not None else InventoryService(catalog_inst)
    payments_inst = payments if payments is not None else PaymentGateway()
    orders_inst = orders if orders is not None else OrderRepository()
    audit_inst = audit if audit is not None else AuditLogger()

    registry = DIRegistry()

    @provider(scope=Scope.SINGLETON)
    def provide_catalog() -> CatalogRepository:
        return catalog_inst

    @provider(scope=Scope.SINGLETON)
    def provide_inventory() -> InventoryService:
        return inventory_inst

    @provider(scope=Scope.SINGLETON)
    def provide_payments() -> PaymentGateway:
        return payments_inst

    @provider(scope=Scope.SINGLETON)
    def provide_orders() -> OrderRepository:
        return orders_inst

    @provider(scope=Scope.SINGLETON)
    def provide_audit() -> AuditLogger:
        return audit_inst

    registry.bind(CatalogRepository, provide_catalog)
    registry.bind(InventoryService, provide_inventory)
    registry.bind(PaymentGateway, provide_payments)
    registry.bind(OrderRepository, provide_orders)
    registry.bind(AuditLogger, provide_audit)

    return registry
