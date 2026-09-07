"""Reference Order Service facade orchestrating capability plans in Agnara 0.1.0a3.

Encapsulates:
- Ahead-of-time startup compilation of ExecutionPlans across namespaces
- DI container lifecycle management (DIContainer.aclose)
- Monotonic deadline and timeout handling
- ExecutionContext and correlation tracking
- Observability via TelemetryHook
"""

from __future__ import annotations

import asyncio
from collections.abc import Mapping
from typing import Any

from agnara.capability.identity import CapabilityId
from agnara.core.di import DIContainer, DIRegistry
from agnara.execution.context import ExecutionContext
from agnara.execution.invocation import Invocation
from agnara.execution.plan import ExecutionPlan
from agnara.execution.result import CanonicalResult, Failure, FailureCode
from agnara.execution.runtime import invoke_result
from agnara.policy import Principal
from agnara.schema.standard import StandardSchemaAdapter

from capabilities import (
    catalog_app,
    inventory_app,
    orders_app,
    payments_app,
)
from domain import (
    InventoryReservation,
    OrderCancellationResult,
    OrderRecord,
    PaymentAuthorization,
    Product,
)
from services import AuditLogger, build_di_registry
from telemetry import AuditLoggingHook, ServiceTelemetryCollector

__all__ = [
    "ReferenceOrderService",
]


class ReferenceOrderService:
    """The central integrating service compiling and executing Agnara capability plans."""

    def __init__(
        self,
        di_registry: DIRegistry | None = None,
        telemetry_collector: ServiceTelemetryCollector | None = None,
        audit_logger: AuditLogger | None = None,
    ) -> None:
        self.di_registry = di_registry if di_registry is not None else build_di_registry()
        self.telemetry = (
            telemetry_collector if telemetry_collector is not None else ServiceTelemetryCollector()
        )
        self.audit_logger = audit_logger if audit_logger is not None else AuditLogger()
        self.audit_hook = AuditLoggingHook(self.audit_logger)

        self.schema_adapter = StandardSchemaAdapter()
        hooks = (self.telemetry, self.audit_hook)

        # 1. Compile registries
        cat_frozen = catalog_app.compile()
        inv_frozen = inventory_app.compile()
        pay_frozen = payments_app.compile()
        ord_frozen = orders_app.compile()

        # 2. Compile execution plans
        self._plans: dict[CapabilityId, ExecutionPlan] = {}

        for definition in [
            cat_frozen.get("catalog.get_product"),
            inv_frozen.get("inventory.reserve"),
            pay_frozen.get("payments.authorize"),
            ord_frozen.get("orders.create"),
            ord_frozen.get("orders.get"),
            ord_frozen.get("orders.cancel"),
        ]:
            plan = ExecutionPlan.compile(
                definition=definition,
                registry=self.di_registry,
                hooks=hooks,
                schema_adapter=self.schema_adapter,
            )
            self._plans[definition.id] = plan

    @property
    def plans(self) -> Mapping[CapabilityId, ExecutionPlan]:
        """Read-only view of compiled execution plans."""
        return self._plans

    async def invoke[T](
        self,
        capability_id: str | CapabilityId,
        payload: dict[str, Any],
        *,
        principal: Principal | None = None,
        tracking_id: str | None = None,
        timeout: float | None = None,
    ) -> CanonicalResult[T]:
        """Execute a compiled capability plan with DI scoping, policies, and telemetry."""
        cap_id = (
            CapabilityId.parse(capability_id) if isinstance(capability_id, str) else capability_id
        )

        plan = self._plans.get(cap_id)
        if plan is None:
            return Failure(
                FailureCode.NOT_FOUND,
                f"capability '{cap_id}' not found in compiled service plans",
            )

        loop = asyncio.get_running_loop()
        deadline = (loop.time() + timeout) if timeout is not None else None
        invocation = Invocation(
            capability_id=plan.definition.id,
            payload=payload,
            metadata={"tracking_id": tracking_id} if tracking_id else {},
            deadline=deadline,
        )

        container = DIContainer(self.di_registry)
        context = ExecutionContext(
            invocation=invocation,
            di_container=container,
            tracking_id=tracking_id,
            principal=principal,
        )

        try:
            return await invoke_result(plan, context)
        finally:
            await container.aclose()

    # -------------------------------------------------------------------------
    # Ergonomic Service Methods
    # -------------------------------------------------------------------------

    async def get_product(
        self,
        sku: str,
        *,
        principal: Principal | None = None,
        tracking_id: str | None = None,
    ) -> CanonicalResult[Product]:
        """Fetch product specification from the catalog."""
        return await self.invoke(
            "catalog.get_product",
            {"sku": sku},
            principal=principal,
            tracking_id=tracking_id,
        )

    async def reserve_stock(
        self,
        order_id: str,
        items: list[dict[str, Any]],
        *,
        principal: Principal | None = None,
        tracking_id: str | None = None,
    ) -> CanonicalResult[InventoryReservation]:
        """Reserve warehouse inventory stock for items."""
        return await self.invoke(
            "inventory.reserve",
            {"order_id": order_id, "items": items},
            principal=principal,
            tracking_id=tracking_id,
        )

    async def authorize_payment(
        self,
        payment_id: str,
        order_id: str,
        customer_id: str,
        amount_cents: int,
        payment_ref: str,
        *,
        principal: Principal | None = None,
        tracking_id: str | None = None,
    ) -> CanonicalResult[PaymentAuthorization]:
        """Simulate fund authorization through the payment gateway."""
        return await self.invoke(
            "payments.authorize",
            {
                "payment_id": payment_id,
                "order_id": order_id,
                "customer_id": customer_id,
                "amount_cents": amount_cents,
                "payment_ref": payment_ref,
            },
            principal=principal,
            tracking_id=tracking_id,
        )

    async def create_order(
        self,
        order_id: str,
        customer_id: str,
        items: list[dict[str, Any]],
        payment_ref: str,
        *,
        principal: Principal | None = None,
        tracking_id: str | None = None,
        timeout: float | None = None,
    ) -> CanonicalResult[OrderRecord]:
        """Execute full transactional order creation workflow."""
        return await self.invoke(
            "orders.create",
            {
                "order_id": order_id,
                "customer_id": customer_id,
                "items": items,
                "payment_ref": payment_ref,
            },
            principal=principal,
            tracking_id=tracking_id,
            timeout=timeout,
        )

    async def get_order(
        self,
        order_id: str,
        *,
        principal: Principal | None = None,
        tracking_id: str | None = None,
    ) -> CanonicalResult[OrderRecord]:
        """Retrieve existing customer order by order_id."""
        return await self.invoke(
            "orders.get",
            {"order_id": order_id},
            principal=principal,
            tracking_id=tracking_id,
        )

    async def cancel_order(
        self,
        order_id: str,
        reason: str,
        *,
        principal: Principal | None = None,
        tracking_id: str | None = None,
    ) -> CanonicalResult[OrderCancellationResult]:
        """Cancel an existing order, releasing reservations and voiding payment."""
        return await self.invoke(
            "orders.cancel",
            {"order_id": order_id, "reason": reason},
            principal=principal,
            tracking_id=tracking_id,
        )
