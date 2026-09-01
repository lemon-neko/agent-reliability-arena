"""Minimal OpenTelemetry bootstrap without exporting sensitive payloads."""

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider


def configure_telemetry() -> None:
    if isinstance(trace.get_tracer_provider(), TracerProvider):
        return
    trace.set_tracer_provider(
        TracerProvider(resource=Resource.create({"service.name": "agent-reliability-arena"}))
    )


tracer = trace.get_tracer("arena.engine")
