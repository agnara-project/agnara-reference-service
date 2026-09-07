"""Domain entities, value objects, enums, and sanitization utilities.

Pure domain models for the Order Management Service (OMS), completely
decoupled from transport protocols, external serialization libraries,
and Agnara framework internals.

EDUCATIONAL DISCLAIMER:
This domain contains an explicitly simulated financial authorization capability.
No real money is moved, no payment gateway is contacted, and no real account
or payment credentials are ever accepted or stored.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

__all__ = [
    "InventoryReservation",
    "OrderCancellationResult",
    "OrderItem",
    "OrderRecord",
    "OrderStatus",
    "PaymentAuthorization",
    "PaymentStatus",
    "Product",
    "ReservationStatus",
    "mask_secret",
]


class OrderStatus(StrEnum):
    """Lifecycle status of an order."""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class ReservationStatus(StrEnum):
    """Lifecycle status of an inventory reservation."""

    RESERVED = "reserved"
    RELEASED = "released"


class PaymentStatus(StrEnum):
    """Lifecycle status of a simulated payment authorization."""

    AUTHORIZED = "authorized"
    VOIDED = "voided"
    CAPTURED = "captured"


@dataclass(slots=True, frozen=True)
class Product:
    """Catalog product definition."""

    sku: str
    name: str
    unit_price_cents: int
    description: str
    category: str
    in_stock: int


@dataclass(slots=True, frozen=True)
class OrderItem:
    """Line item within an order or reservation request."""

    sku: str
    quantity: int
    unit_price_cents: int

    @property
    def total_cents(self) -> int:
        """Total price for this line item in cents."""
        return self.quantity * self.unit_price_cents


@dataclass(slots=True, frozen=True)
class InventoryReservation:
    """Record of stock held for a pending order."""

    reservation_id: str
    order_id: str
    items: tuple[OrderItem, ...]
    status: ReservationStatus


@dataclass(slots=True, frozen=True)
class PaymentAuthorization:
    """Simulated record of authorized funds.

    Demonstration only: no external processor was contacted and no money was moved.
    """

    authorization_id: str
    order_id: str
    customer_id: str
    amount_cents: int
    status: PaymentStatus
    sanitized_ref: str
    provider_ref: str


@dataclass(slots=True, frozen=True)
class OrderRecord:
    """Full persistent representation of a customer order."""

    order_id: str
    customer_id: str
    items: tuple[OrderItem, ...]
    total_cents: int
    status: OrderStatus
    reservation_id: str | None
    authorization_id: str | None
    created_at: str
    tracking_id: str | None


@dataclass(slots=True, frozen=True)
class OrderCancellationResult:
    """Canonical outcome of an order cancellation."""

    order_id: str
    status: OrderStatus
    reason: str
    released_reservation_id: str | None
    voided_authorization_id: str | None


def mask_secret(reference: str) -> str:
    """Mask sensitive authorization reference for safe diagnostic logging."""
    if not isinstance(reference, str) or len(reference) <= 4:
        return "***"
    if reference.startswith("sim-ref-"):
        suffix = reference[-4:]
        return f"sim-***{suffix}"
    return f"***{reference[-4:]}"
