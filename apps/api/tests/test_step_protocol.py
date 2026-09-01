from __future__ import annotations

import httpx
import pytest

from arena.domain.risk import AgentNetworkScope, AgentTarget
from arena.runtime.step_protocol import (
    MAX_RESPONSE_BYTES,
    FinalResponse,
    HTTPAgentClient,
    StepLimits,
    StepMessage,
    StepProtocolError,
    StepProtocolTimeout,
    StepRequest,
)


def request() -> StepRequest:
    return StepRequest(
        run_id="run-1",
        step=1,
        messages=[StepMessage(role="user", content="hello")],
        tools=[],
        limits=StepLimits(remaining_steps=1, deadline_ms=1_000),
    )


def local_target() -> AgentTarget:
    return AgentTarget(
        id="target-1",
        name="Local",
        endpoint_url="http://127.0.0.1:9000/step",
        network_scope=AgentNetworkScope.LOCAL,
    )


def test_http_agent_client_accepts_strict_final_response() -> None:
    transport = httpx.MockTransport(
        lambda incoming: httpx.Response(
            200,
            json={"type": "final", "output": "ready"},
            headers={"Content-Type": "application/json"},
        )
    )
    result = HTTPAgentClient(local_target(), transport=transport).step(request())
    assert isinstance(result, FinalResponse)
    assert result.output == "ready"


@pytest.mark.parametrize(
    ("body", "content_type", "message"),
    [
        (b"not-json", "application/json", "invalid"),
        (b"{}", "text/plain", "application/json"),
        (b'{"type":"final","output":"ok","unexpected":true}', "application/json", "invalid"),
        (b"x" * (MAX_RESPONSE_BYTES + 1), "application/json", "1 MB"),
    ],
)
def test_http_agent_client_rejects_invalid_or_oversized_responses(
    body: bytes, content_type: str, message: str
) -> None:
    transport = httpx.MockTransport(
        lambda incoming: httpx.Response(
            200,
            content=body,
            headers={"Content-Type": content_type},
        )
    )
    with pytest.raises(StepProtocolError, match=message):
        HTTPAgentClient(local_target(), transport=transport).step(request())


def test_public_scope_rejects_private_addresses_before_request() -> None:
    target = AgentTarget(
        id="target-public",
        name="Invalid public",
        endpoint_url="https://127.0.0.1/step",
        network_scope=AgentNetworkScope.PUBLIC,
    )
    with pytest.raises(StepProtocolError, match="forbidden address"):
        HTTPAgentClient(target).validate_network_policy()


def test_http_status_redirect_and_timeout_fail_closed() -> None:
    redirect = httpx.MockTransport(
        lambda incoming: httpx.Response(307, headers={"Location": "http://127.0.0.1/other"})
    )
    with pytest.raises(StepProtocolError, match="failed safely"):
        HTTPAgentClient(local_target(), transport=redirect).step(request())

    def timeout(incoming: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("synthetic timeout", request=incoming)

    with pytest.raises(StepProtocolTimeout, match="HTTP timeout"):
        HTTPAgentClient(local_target(), transport=httpx.MockTransport(timeout)).step(request())
