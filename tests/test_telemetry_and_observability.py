"""Tests for TelemetryHook lifecycle observers, latency, and correlation."""

from __future__ import annotations

import asyncio

from agnara.execution.result import Success
from agnara.policy import Principal

from service import ReferenceOrderService
from telemetry import ServiceTelemetryCollector


def test_telemetry_lifecycle_events_and_pairing() -> None:
    """TelemetryHook correctly records lifecycle start and terminal events."""

    async def _run() -> None:
        collector = ServiceTelemetryCollector()
        service = ReferenceOrderService(telemetry_collector=collector)

        user = Principal(identity="alice", scopes=["catalog:read"])
        res = await service.get_product(
            "SKU-KEYBOARD-02", principal=user, tracking_id="trk-telemetry-1"
        )
        assert isinstance(res, Success)

        records = collector.get_records()
        assert len(records) == 1
        rec = records[0]

        assert rec.capability_id == "catalog.get_product"
        assert rec.tracking_id == "trk-telemetry-1"
        assert len(rec.invocation_id) == 32  # UUID4 hex length
        assert rec.duration_ns > 0
        assert rec.duration_ms >= 0.0
        assert rec.outcome == "success"

    asyncio.run(_run())


def test_tracking_id_filtering_and_propagation() -> None:
    """Telemetry collector allows querying records filtered by specific tracking IDs."""

    async def _run() -> None:
        collector = ServiceTelemetryCollector()
        service = ReferenceOrderService(telemetry_collector=collector)

        user = Principal(identity="alice", scopes=["catalog:read"])
        await service.get_product("SKU-LAPTOP-01", principal=user, tracking_id="trk-alpha")
        await service.get_product("SKU-MOUSE-03", principal=user, tracking_id="trk-beta")

        alpha_records = collector.get_records("trk-alpha")
        beta_records = collector.get_records("trk-beta")

        assert len(alpha_records) == 1
        assert alpha_records[0].tracking_id == "trk-alpha"

        assert len(beta_records) == 1
        assert beta_records[0].tracking_id == "trk-beta"

    asyncio.run(_run())
