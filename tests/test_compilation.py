"""Tests for capability plan compilation, DI graph verification, and hook validation."""

from __future__ import annotations

import pytest
from agnara.capability.identity import CapabilityId
from agnara.errors import DefinitionError
from agnara.execution.plan import ExecutionPlan
from agnara.schema.standard import StandardSchemaAdapter

from capabilities import (
    catalog_app,
    inventory_app,
    orders_app,
    payments_app,
)
from services import (
    build_di_registry,
)


def test_startup_plan_compilation() -> None:
    """All 6 core capability plans compile ahead-of-time without errors."""
    di_registry = build_di_registry()
    adapter = StandardSchemaAdapter()

    cat_reg = catalog_app.compile()
    inv_reg = inventory_app.compile()
    pay_reg = payments_app.compile()
    ord_reg = orders_app.compile()

    capabilities_to_compile = [
        cat_reg.get("catalog.get_product"),
        inv_reg.get("inventory.reserve"),
        pay_reg.get("payments.authorize"),
        ord_reg.get("orders.create"),
        ord_reg.get("orders.get"),
        ord_reg.get("orders.cancel"),
    ]

    assert len(capabilities_to_compile) == 6

    compiled_plans: dict[CapabilityId, ExecutionPlan] = {}
    for cap in capabilities_to_compile:
        plan = ExecutionPlan.compile(
            definition=cap,
            registry=di_registry,
            schema_adapter=adapter,
        )
        assert isinstance(plan, ExecutionPlan)
        compiled_plans[cap.id] = plan

    assert len(compiled_plans) == 6


def test_dependency_injection_dag_resolution() -> None:
    """Compiled plans correctly identify their injected dependency parameters."""
    di_registry = build_di_registry()

    cat_reg = catalog_app.compile()
    plan_catalog = ExecutionPlan.compile(
        definition=cat_reg.get("catalog.get_product"),
        registry=di_registry,
    )
    assert "catalog" in plan_catalog.dependency_parameters

    ord_reg = orders_app.compile()
    plan_create = ExecutionPlan.compile(
        definition=ord_reg.get("orders.create"),
        registry=di_registry,
    )
    # orders.create requires 5 injected services
    for dep in ["catalog", "inventory", "gateway", "orders", "audit"]:
        assert dep in plan_create.dependency_parameters


def test_protected_context_parameters() -> None:
    """ExecutionContext parameters are identified as protected runtime-owned parameters."""
    di_registry = build_di_registry()
    ord_reg = orders_app.compile()

    plan_create = ExecutionPlan.compile(
        definition=ord_reg.get("orders.create"),
        registry=di_registry,
    )
    assert "ctx" in plan_create.context_parameters
    assert "ctx" in plan_create.protected_parameters


def test_async_telemetry_hook_rejection() -> None:
    """ExecutionPlan compile rejects asynchronous coroutine telemetry hooks."""
    di_registry = build_di_registry()
    cat_reg = catalog_app.compile()

    class AsyncHook:
        async def on_invocation_start(self, event: object) -> None:
            pass

        def on_invocation_terminal(self, event: object) -> None:
            pass

    with pytest.raises(DefinitionError) as exc_info:
        ExecutionPlan.compile(
            definition=cat_reg.get("catalog.get_product"),
            registry=di_registry,
            hooks=(AsyncHook(),),  # type: ignore[arg-type]
        )
    assert "must be synchronous and non-generating" in str(exc_info.value)
