"""Tests verifying zero sensitive data leakage, PII protection, and failure immutability."""

from __future__ import annotations

import asyncio
from types import MappingProxyType

import pytest
from agnara.execution.result import Failure
from agnara.policy import Principal

from domain import mask_secret
from service import ReferenceOrderService


def test_mask_secret_utility() -> None:
    """mask_secret utility properly masks credentials while preserving safe prefixes."""
    assert mask_secret("sim-ref-corporate-4242") == "sim-***4242"
    assert mask_secret("secret_token_9999") == "***9999"
    assert mask_secret("123") == "***"
    assert mask_secret("") == "***"


def test_zero_raw_token_leakage_in_telemetry_and_audit() -> None:
    """Raw payment references never leak into audit records or telemetry events."""

    async def _run() -> None:
        service = ReferenceOrderService()
        user = Principal(
            identity="alice",
            scopes=["catalog:read", "orders:write", "payments:write", "inventory:write"],
        )

        sensitive_token = "sim-ref-super-secret-corporate-4242"

        await service.create_order(
            order_id="ORD-SEC-01",
            customer_id="CUST-SEC",
            items=[{"sku": "SKU-KEYBOARD-02", "quantity": 1}],
            payment_ref=sensitive_token,
            principal=user,
            tracking_id="trk-security-check",
        )

        # Invariant 1: No raw token in Telemetry records
        telemetry_dump = str([r for r in service.telemetry.get_records()])
        assert sensitive_token not in telemetry_dump

        # Invariant 2: No raw token in AuditLogger records
        audit_dump = str(service.audit_logger.get_records())
        assert sensitive_token not in audit_dump

    asyncio.run(_run())


def test_failure_details_immutability() -> None:
    """Failure.details is an immutable MappingProxyType, preventing runtime mutation."""

    async def _run() -> None:
        service = ReferenceOrderService()
        user = Principal(identity="alice", scopes=["orders:write", "catalog:read"])

        # Trigger failure via empty items list
        res = await service.create_order(
            order_id="ORD-IMMUTABLE-FAIL",
            customer_id="CUST-1",
            items=[],
            payment_ref="sim-ref-standard-99",
            principal=user,
        )
        assert isinstance(res, Failure)
        assert isinstance(res.details, MappingProxyType)

        # Attempt mutation must raise TypeError
        with pytest.raises(TypeError):
            res.details["injected_key"] = "malicious_payload"  # type: ignore[index]

    asyncio.run(_run())
