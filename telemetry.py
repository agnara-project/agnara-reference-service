"""In-process observability, lifecycle telemetry hooks, and secret-safe recording.

Implements the agnara.execution.telemetry.TelemetryHook protocol.
Demonstrates:
1. Event pairing via UUID4 invocation_id (not tracking_id).
2. Monotonic high-resolution duration measurement (duration_ns).
3. Cross-capability correlation via caller tracking_id.
4. Absolute secret redaction: hooks never receive execution payloads.
"""

from __future__ import annotations

from dataclasses import dataclass

from agnara.execution.telemetry import (
    InvocationStartEvent,
    InvocationTerminalEvent,
    TelemetryHook,
)

from services import AuditLogger

__all__ = [
    "AuditLoggingHook",
    "ServiceTelemetryCollector",
    "TelemetryRecord",
]


@dataclass(slots=True, frozen=True)
class TelemetryRecord:
    """Immutable record of an observed capability execution."""

    capability_id: str
    tracking_id: str | None
    invocation_id: str
    duration_ns: int
    duration_ms: float
    outcome: str


class ServiceTelemetryCollector(TelemetryHook):
    """Real-time in-process telemetry collector observing Agnara execution hooks."""

    def __init__(self) -> None:
        self._active: dict[str, InvocationStartEvent] = {}
        self._records: list[TelemetryRecord] = []

    def on_invocation_start(self, event: InvocationStartEvent) -> None:
        """Invoked immediately before capability execution begins."""
        self._active[event.invocation_id] = event

    def on_invocation_terminal(self, event: InvocationTerminalEvent) -> None:
        """Invoked immediately after capability execution terminates (success/failure/timeout)."""
        self._active.pop(event.invocation_id, None)
        record = TelemetryRecord(
            capability_id=str(event.capability_id),
            tracking_id=event.tracking_id,
            invocation_id=event.invocation_id,
            duration_ns=event.duration_ns,
            duration_ms=round(event.duration_ns / 1_000_000, 3),
            outcome=event.outcome,
        )
        self._records.append(record)

    def get_records(self, tracking_id: str | None = None) -> list[TelemetryRecord]:
        """Fetch recorded telemetry entries, optionally filtered by tracking ID."""
        if tracking_id is None:
            return list(self._records)
        return [r for r in self._records if r.tracking_id == tracking_id]

    def clear(self) -> None:
        """Clear all recorded telemetry."""
        self._active.clear()
        self._records.clear()


class AuditLoggingHook(TelemetryHook):
    """Bridges Agnara runtime lifecycle events into the business audit log."""

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self.audit_logger = audit_logger

    def on_invocation_start(self, event: InvocationStartEvent) -> None:
        """Telemetry start observer (payload-free)."""
        pass

    def on_invocation_terminal(self, event: InvocationTerminalEvent) -> None:
        """Record lifecycle completion in the audit logger."""
        if self.audit_logger is not None:
            duration_ms = round(event.duration_ns / 1_000_000, 3)
            self.audit_logger.record(
                event.tracking_id,
                str(event.capability_id),
                f"Capability execution finished with outcome '{event.outcome}'",
                invocation_id=event.invocation_id,
                duration_ms=duration_ms,
                outcome=event.outcome,
            )
