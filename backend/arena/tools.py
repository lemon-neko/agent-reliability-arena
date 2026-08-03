"""Restricted tool gateway. There is deliberately no shell or general HTTP tool."""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from arena.domain import ScenarioSpec
from arena.sandbox import RunSandbox, SandboxViolation


class ToolError(RuntimeError):
    pass


class ApprovalRequired(ToolError):
    def __init__(self, tool: str, arguments: dict[str, Any], reason: str) -> None:
        self.tool = tool
        self.arguments = arguments
        self.reason = reason
        super().__init__(reason)


class ToolAdapter(Protocol):
    name: str

    def invoke(self, arguments: dict[str, Any]) -> dict[str, Any]: ...


@dataclass
class FileTool:
    sandbox: RunSandbox
    name: str = "file"

    def invoke(self, arguments: dict[str, Any]) -> dict[str, Any]:
        operation = str(arguments.get("operation", ""))
        relative = str(arguments.get("path", ""))
        if operation == "list":
            target = self.sandbox.resolve(relative or ".", must_exist=True)
            if not target.is_dir():
                raise ToolError("list target is not a directory")
            return {"entries": sorted(path.name for path in target.iterdir())}
        if operation == "read":
            target = self.sandbox.resolve(relative, must_exist=True)
            if not target.is_file():
                raise ToolError("read target is not a file")
            return {"content": target.read_text(encoding="utf-8")[:100_000]}
        if operation == "write":
            target = self.sandbox.resolve(relative)
            target.parent.mkdir(parents=True, exist_ok=True)
            # Parent directories may themselves contain a malicious symlink.
            checked = target.parent.resolve()
            if not checked.is_relative_to(self.sandbox.workspace.resolve()):
                raise SandboxViolation("write parent escapes run sandbox")
            content = str(arguments.get("content", ""))[:100_000]
            target.write_text(content, encoding="utf-8")
            return {
                "path": target.relative_to(self.sandbox.workspace).as_posix(),
                "bytes": len(content.encode()),
            }
        raise ToolError("unsupported file operation")


@dataclass
class SQLTool:
    sandbox: RunSandbox
    name: str = "sql"

    def invoke(self, arguments: dict[str, Any]) -> dict[str, Any]:
        statement = str(arguments.get("statement", "")).strip()
        parameters = arguments.get("parameters", [])
        if not statement or len(statement) > 20_000 or not isinstance(parameters, list):
            raise ToolError("invalid SQL request")
        keyword = statement.split(maxsplit=1)[0].upper()
        if keyword in {"ATTACH", "DETACH", "PRAGMA", "VACUUM", "CREATE", "DROP", "ALTER"}:
            raise ToolError("SQL operation is outside the scenario policy")
        with sqlite3.connect(self.sandbox.database) as connection:
            connection.row_factory = sqlite3.Row
            try:
                cursor = connection.execute(statement, tuple(parameters))
                if keyword in {"SELECT", "WITH"}:
                    rows = [dict(row) for row in cursor.fetchmany(100)]
                    return {"rows": rows, "row_count": len(rows)}
                if keyword in {"UPDATE", "INSERT", "DELETE"}:
                    if bool(arguments.get("dry_run", False)):
                        connection.rollback()
                        return {"row_count": cursor.rowcount, "rolled_back": True}
                    connection.commit()
                    return {"row_count": cursor.rowcount, "committed": True}
            except sqlite3.Error as error:
                connection.rollback()
                raise ToolError(f"SQL transaction rolled back: {type(error).__name__}") from error
        raise ToolError("SQL statement is not allowed")


@dataclass
class RetrievalTool:
    documents_root: Path
    name: str = "retrieval"

    def invoke(self, arguments: dict[str, Any]) -> dict[str, Any]:
        query = str(arguments.get("query", ""))[:1000]
        if not query.strip():
            raise ToolError("query is required")
        tokens = set(re.findall(r"[\w\u4e00-\u9fff]+", query.lower()))
        matches: list[tuple[int, str, str]] = []
        for path in sorted(self.documents_root.rglob("*.md")):
            text = path.read_text(encoding="utf-8")[:100_000]
            score = sum(token in text.lower() for token in tokens)
            matches.append((score, path.name, text))
        selected = sorted(matches, reverse=True)[: max(1, min(int(arguments.get("limit", 3)), 5))]
        return {
            "chunks": [
                {"source": source, "content": content, "score": score}
                for score, source, content in selected
                if score > 0
            ]
        }


@dataclass
class ApprovalTool:
    name: str = "approval"

    def invoke(self, arguments: dict[str, Any]) -> dict[str, Any]:
        raise ApprovalRequired(
            "approval",
            arguments,
            str(arguments.get("reason", "Sensitive action requires human approval"))[:500],
        )


@dataclass
class SecretTool:
    secrets: dict[str, str]
    name: str = "secret"

    def invoke(self, arguments: dict[str, Any]) -> dict[str, Any]:
        action = str(arguments.get("action", ""))
        if action != "exists":
            raise ToolError("secret values are never readable by agents")
        return {"exists": str(arguments.get("name", "")) in self.secrets}


@dataclass
class ToolGateway:
    scenario: ScenarioSpec
    sandbox: RunSandbox
    approved: bool = False
    tools: dict[str, ToolAdapter] = field(init=False)

    def __post_init__(self) -> None:
        self.tools = {
            "file": FileTool(self.sandbox),
            "sql": SQLTool(self.sandbox),
            "retrieval": RetrievalTool(self.sandbox.documents),
            "approval": ApprovalTool(),
            "secret": SecretTool(self.scenario.fixtures.secrets),
        }

    def invoke(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if name not in self.scenario.allowed_tools or name not in self.tools:
            raise ToolError(f"tool is not allowed in this scenario: {name}")
        if _contains_control_characters(arguments):
            raise ToolError("tool arguments contain control characters")
        if name == "approval" and self.approved:
            return {"approved": True, "decision": "human-approved"}
        return self.tools[name].invoke(arguments)


def _contains_control_characters(value: Any) -> bool:
    if isinstance(value, str):
        return any(ord(char) < 9 or 13 < ord(char) < 32 for char in value)
    if isinstance(value, dict):
        return any(
            _contains_control_characters(key) or _contains_control_characters(item)
            for key, item in value.items()
        )
    if isinstance(value, list):
        return any(_contains_control_characters(item) for item in value)
    return False
