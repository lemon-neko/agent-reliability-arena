"""Canonical, sanitized report exports for humans and public attestations."""

from __future__ import annotations

import hashlib
import html
import json
from uuid import uuid4

from arena.domain.risk import AssessmentProfile, Attestation, RiskReport


def canonical_report_json(report: RiskReport) -> str:
    return json.dumps(
        report.model_dump(mode="json"),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def create_attestation(report: RiskReport) -> Attestation:
    if report.profile != AssessmentProfile.STANDARD:
        raise ValueError("public attestations require the Standard profile")
    if not report.repository_url:
        raise ValueError("public attestations require a repository_url")
    digest = hashlib.sha256(canonical_report_json(report).encode()).hexdigest()
    return Attestation(
        id=f"attestation-{uuid4().hex[:12]}",
        agent_name=report.target_name,
        agent_version=report.target_version,
        repository_url=report.repository_url,
        suite_version=report.suite_version,
        score=report.final_score,
        grade=report.grade,
        verdict=report.verdict,
        finding_counts=report.finding_counts,
        volatility_percent=float(report.coverage.get("volatility_percent", 0)),
        report_sha256=digest,
        evaluated_at=report.generated_at,
    )


def render_risk_report(report: RiskReport) -> str:
    dimensions = "".join(
        f"<tr><td>{_dimension_label(name)}</td><td>{value:.2f}</td></tr>"
        for name, value in report.dimension_scores.model_dump().items()
    )
    findings = "".join(
        "<article class='finding'>"
        f"<div><span class='severity {item.severity.value}'>{item.severity.value}</span>"
        f"<code>{html.escape(item.case_id)}</code></div>"
        f"<h3>{html.escape(item.title)}</h3>"
        f"<p>{html.escape(item.summary)}</p>"
        f"<dl><dt>期望</dt><dd>{html.escape(item.expected)}</dd>"
        f"<dt>实际</dt><dd>{html.escape(item.observed)}</dd>"
        f"<dt>修复建议</dt><dd>{html.escape(item.remediation)}</dd>"
        f"<dt>复现</dt><dd><code>{html.escape(item.reproduction)}</code></dd></dl>"
        f"<small>出现 {item.occurrences} 次 · 确定性证据</small>"
        "</article>"
        for item in report.findings
    ) or "<p class='empty'>没有发现违反当前测试包确定性规则的行为。</p>"
    gates = "".join(f"<li>{html.escape(item)}</li>" for item in report.gate_reasons)
    limitations = "".join(f"<li>{html.escape(item)}</li>" for item in report.limitations)
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>{html.escape(report.target_name)} 风险体检报告</title>
<style>
:root{{--ink:#17201c;--muted:#647069;--paper:#f3f0e8;--line:#cbc9bf;--accent:#0f6b4c;--danger:#a53c2b}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--paper);color:var(--ink);font:15px/1.65 system-ui,sans-serif}}
main{{max-width:980px;margin:auto;padding:64px 42px}}header{{display:grid;grid-template-columns:1fr auto;gap:40px;border-bottom:2px solid var(--ink);padding-bottom:32px}}
h1{{font-size:44px;line-height:1.05;letter-spacing:-.04em;margin:12px 0}}h2{{margin-top:52px}}.kicker,code{{font-family:ui-monospace,monospace}}.kicker{{color:var(--accent);font-size:12px;letter-spacing:.12em}}
.grade{{font:700 96px/1 ui-monospace,monospace;color:var(--accent)}}.score{{font:600 22px ui-monospace,monospace;text-align:right}}.verdict{{font-weight:700;color:var(--danger)}}
.summary{{display:grid;grid-template-columns:1fr 1fr;gap:36px;margin-top:36px}}table{{width:100%;border-collapse:collapse}}td{{padding:10px 0;border-bottom:1px solid var(--line)}}td:last-child{{text-align:right;font-family:ui-monospace,monospace}}
.finding{{border-top:1px solid var(--line);padding:24px 0;break-inside:avoid}}.finding>div{{display:flex;justify-content:space-between}}.finding h3{{font-size:22px;margin:12px 0 4px}}.severity{{text-transform:uppercase;font:700 11px ui-monospace,monospace;color:var(--danger)}}
dl{{display:grid;grid-template-columns:100px 1fr;gap:8px 18px}}dt{{color:var(--muted)}}dd{{margin:0}}small,.empty{{color:var(--muted)}}footer{{margin-top:60px;border-top:1px solid var(--line);padding-top:18px;color:var(--muted)}}
@media(max-width:700px){{main{{padding:32px 20px}}header,.summary{{grid-template-columns:1fr}}.grade{{font-size:68px}}}}
@media print{{body{{background:white}}main{{padding:20px}}}}
</style></head><body><main>
<header><div><span class="kicker">AGENT RELIABILITY ARENA · RISK REPORT V1</span><h1>{html.escape(report.target_name)}</h1>
<p>{html.escape(report.target_version)} · {html.escape(report.suite_version)} · {report.profile.value}</p>
<strong class="verdict">{_verdict_label(report.verdict.value)}</strong></div><div><div class="grade">{report.grade}</div><div class="score">{report.final_score:.2f} / 100</div></div></header>
<section class="summary"><div><h2>管理摘要</h2><p>原始分 {report.raw_score:.2f}，门禁后得分 {report.final_score:.2f}。完成 {report.coverage.get('completed_runs', 0)} / {report.coverage.get('total_runs', 0)} 次运行；通过率 {report.coverage.get('pass_rate_percent', 0)}%，波动性 {report.coverage.get('volatility_percent', 0)}%。</p>
<ul>{gates or '<li>未触发 High 或 Critical 安全门禁。</li>'}</ul></div><div><h2>维度得分</h2><table>{dimensions}</table></div></section>
<section><h2>技术发现 · {len(report.findings)}</h2>{findings}</section>
<section><h2>适用边界</h2><ul>{limitations}</ul></section>
<footer>生成时间：{report.generated_at.isoformat()} · Assessment {html.escape(report.assessment_id)}</footer>
</main></body></html>"""


def _dimension_label(value: str) -> str:
    return {
        "security_privacy": "安全与隐私 / 25",
        "authorization_control": "权限与人工控制 / 20",
        "side_effect_safety": "工具与副作用 / 15",
        "correctness_grounding": "正确性与证据 / 15",
        "resilience_idempotency": "恢复与幂等 / 15",
        "efficiency_resources": "效率与资源 / 10",
    }[value]


def _verdict_label(value: str) -> str:
    return {
        "ready": "建议上线",
        "conditional": "有条件上线",
        "not_recommended": "不建议上线",
    }[value]
