"""Policy guardrails and verification rules for the reference order service.

Implements the agnara.policy.Policy protocol to enforce operational safety
and authorization rules before capability handlers are invoked by the runtime.
"""

from __future__ import annotations

from dataclasses import dataclass

from agnara.execution.context import ExecutionContext
from agnara.policy import PolicyFailure, PolicyResult, PolicySuccess

from services import CatalogRepository

__all__ = [
    "OrderCancellationPolicy",
    "PaymentSpendingLimitPolicy",
]


@dataclass(slots=True, frozen=True)
class PaymentSpendingLimitPolicy:
    """Guardrail enforcing a maximum transaction amount limit.

    If amount_cents exceeds max_amount_cents, execution is denied with
    a PolicyFailure unless the principal possesses the 'payments:unlimited' scope.
    """

    max_amount_cents: int = 500_000  # Default $5,000.00 limit

    async def evaluate(self, context: ExecutionContext) -> PolicyResult:
        payload = context.invocation.payload
        amount_cents = payload.get("amount_cents")

        # In orders.create, payload has items, so calculate total if amount_cents not present
        if amount_cents is None and "items" in payload:
            items = payload.get("items")
            if isinstance(items, list):
                total = 0
                catalog: CatalogRepository | None = None
                if context.di_container.registry.is_bound(CatalogRepository):
                    provider_def = context.di_container.registry.get_provider(CatalogRepository)
                    catalog = provider_def.func()

                for item in items:
                    if isinstance(item, dict):
                        qty = int(item.get("quantity", 0))
                        unit_price = item.get("unit_price_cents")
                        if unit_price is None and catalog is not None:
                            sku = str(item.get("sku", ""))
                            prod = catalog.get_product(sku)
                            if prod is not None:
                                unit_price = prod.unit_price_cents
                        total += qty * int(unit_price or 0)
                amount_cents = total

        if isinstance(amount_cents, (int, float)):
            if amount_cents > self.max_amount_cents:
                principal = context.principal
                if principal is None or "payments:unlimited" not in principal.scopes:
                    return PolicyFailure(
                        f"transaction amount {int(amount_cents)} cents exceeds "
                        f"spending limit of {self.max_amount_cents} cents"
                    )

        return PolicySuccess()


@dataclass(slots=True, frozen=True)
class OrderCancellationPolicy:
    """Guardrail enforcing business integrity rules on order cancellations.

    Ensures that high-risk destructive cancellations provide an explicit
    audit explanation of at least min_reason_length characters.
    """

    min_reason_length: int = 5

    async def evaluate(self, context: ExecutionContext) -> PolicyResult:
        payload = context.invocation.payload
        reason = payload.get("reason")

        if not isinstance(reason, str) or len(reason.strip()) < self.min_reason_length:
            return PolicyFailure(
                f"cancellation reason must be at least {self.min_reason_length} characters"
            )

        return PolicySuccess()
