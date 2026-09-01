"""Strict HTTP boundary for customer-owned Agent endpoints."""

from __future__ import annotations

import ipaddress
import os
import socket
from typing import Any, Literal, Protocol
from urllib.parse import urlparse

import httpx
from pydantic import BaseModel, ConfigDict, Field, TypeAdapter

from arena.domain.risk import AgentNetworkScope, AgentTarget

MAX_RESPONSE_BYTES = 1_000_000


class StepMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Literal["system", "user", "assistant", "tool"]
    content: str
    tool_call_id: str | None = None


class StepLimits(BaseModel):
    model_config = ConfigDict(extra="forbid")

    remaining_steps: int = Field(ge=0, le=30)
    deadline_ms: int = Field(gt=0, le=120_000)


class StepRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    protocol: Literal["ara-step/1"] = "ara-step/1"
    run_id: str
    step: int = Field(ge=1, le=30)
    messages: list[StepMessage]
    tools: list[dict[str, Any]]
    limits: StepLimits


class ToolCallResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["tool_call"]
    call_id: str = Field(min_length=1, max_length=120)
    name: str = Field(min_length=1, max_length=80)
    arguments: dict[str, Any] = Field(default_factory=dict)


class FinalResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["final"]
    output: str = Field(max_length=200_000)


StepResponse = ToolCallResponse | FinalResponse
STEP_RESPONSE_ADAPTER = TypeAdapter(StepResponse)


class StepProtocolError(RuntimeError):
    pass


class StepProtocolTimeout(StepProtocolError):
    pass


class StepClient(Protocol):
    def step(self, request: StepRequest) -> StepResponse: ...


class HTTPAgentClient:
    def __init__(
        self,
        target: AgentTarget,
        *,
        timeout_seconds: float = 30,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.target = target
        self.timeout_seconds = timeout_seconds
        self.transport = transport

    def validate_network_policy(self) -> None:
        parsed = urlparse(self.target.endpoint_url)
        hostname = parsed.hostname or ""
        if self.target.network_scope == AgentNetworkScope.LOCAL:
            if hostname not in {"localhost", "127.0.0.1", "::1"}:
                raise StepProtocolError("local scope only permits loopback Agent endpoints")
            if hostname == "localhost":
                try:
                    addresses = {
                        ipaddress.ip_address(item[4][0])
                        for item in socket.getaddrinfo(
                            hostname,
                            parsed.port or 80,
                            type=socket.SOCK_STREAM,
                        )
                    }
                except (OSError, ValueError) as error:
                    raise StepProtocolError("localhost DNS resolution failed") from error
                if not addresses or any(not address.is_loopback for address in addresses):
                    raise StepProtocolError("localhost resolved outside loopback")
            return
        if parsed.scheme != "https":
            raise StepProtocolError("public Agent endpoints require HTTPS")
        try:
            addresses = {
                ipaddress.ip_address(item[4][0])
                for item in socket.getaddrinfo(
                    hostname,
                    parsed.port or 443,
                    type=socket.SOCK_STREAM,
                )
            }
        except (OSError, ValueError) as error:
            raise StepProtocolError("Agent endpoint DNS resolution failed") from error
        if not addresses or any(
            address.is_private
            or address.is_loopback
            or address.is_link_local
            or address.is_reserved
            or address.is_multicast
            or address.is_unspecified
            for address in addresses
        ):
            raise StepProtocolError(
                "public Agent endpoint resolved to a forbidden address"
            )

    def step(self, request: StepRequest) -> StepResponse:
        self.validate_network_policy()
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-ARA-Protocol": "ara-step/1",
        }
        if self.target.auth_env_var and self.target.auth_header_name:
            secret = os.getenv(self.target.auth_env_var, "")
            if not secret:
                raise StepProtocolError(
                    f"Agent credential environment variable is not set: {self.target.auth_env_var}"
                )
            headers[self.target.auth_header_name] = secret
        content = bytearray()
        try:
            with httpx.Client(
                timeout=min(self.timeout_seconds, request.limits.deadline_ms / 1000),
                follow_redirects=False,
                transport=self.transport,
                trust_env=False,
            ) as client, client.stream(
                "POST",
                self.target.endpoint_url,
                headers=headers,
                content=request.model_dump_json(),
            ) as response:
                response.raise_for_status()
                content_type = response.headers.get("content-type", "").split(";", 1)[0].strip()
                if content_type != "application/json":
                    raise StepProtocolError("Agent response must use application/json")
                for chunk in response.iter_bytes():
                    if len(content) + len(chunk) > MAX_RESPONSE_BYTES:
                        raise StepProtocolError("Agent response exceeded the 1 MB limit")
                    content.extend(chunk)
        except httpx.TimeoutException as error:
            raise StepProtocolTimeout("Agent step exceeded its HTTP timeout") from error
        except httpx.HTTPError as error:
            message = f"Agent request failed safely: {type(error).__name__}"
            raise StepProtocolError(message) from error
        try:
            return STEP_RESPONSE_ADAPTER.validate_json(content)
        except ValueError as error:
            raise StepProtocolError(
                "Agent returned an invalid ara-step/1 response"
            ) from error

    def check_contract(self) -> dict[str, Any]:
        response = self.step(
            StepRequest(
                run_id="contract-check",
                step=1,
                messages=[
                    StepMessage(
                        role="system",
                        content="This is a protocol check. Return a final response without tools.",
                    ),
                    StepMessage(
                        role="user",
                        content="Reply that the ara-step/1 contract is ready.",
                    ),
                ],
                tools=[],
                limits=StepLimits(remaining_steps=1, deadline_ms=5_000),
            )
        )
        if not isinstance(response, FinalResponse):
            raise StepProtocolError("contract check must return a final response")
        return {"valid": True, "protocol": "ara-step/1", "response": response.output[:200]}
