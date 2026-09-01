import { DEMO_MODE } from "../../shared/api";
import type { RiskReport } from "../../shared/types";

const dimensions = [
  ["security_privacy", "安全与隐私", 25],
  ["authorization_control", "权限与人工控制", 20],
  ["side_effect_safety", "工具与副作用", 15],
  ["correctness_grounding", "正确性与证据", 15],
  ["resilience_idempotency", "恢复与幂等", 15],
  ["efficiency_resources", "效率与资源", 10],
] as const;

export function RiskReportView({ report }: { report: RiskReport | null }) {
  if (!report) return <section className="workspace-page"><header className="page-heading"><div><span className="section-index">RISK REPORTS</span><h1>风险报告</h1><p>完成一次评测后生成管理摘要、技术证据和修复建议。</p></div></header><div className="empty-state large"><b>□</b><h2>尚未生成报告</h2><p>Standard 评测完成后还可以导出公开证明包。</p></div></section>;
  const verdict = { ready: "建议上线", conditional: "有条件上线", not_recommended: "不建议上线" }[report.verdict];
  return (
    <section className="workspace-page report-page">
      <header className="report-masthead"><div><span className="section-index">RISK REPORT / {report.suite_version}</span><h1>{report.target_name}</h1><p>{report.target_version} · {report.profile} · {new Date(report.generated_at).toLocaleString("zh-CN")}</p><strong className={`verdict verdict-${report.verdict}`}>{verdict}</strong></div><div className="report-grade"><b>{report.grade}</b><span>{report.final_score}<small>/100</small></span></div></header>
      {report.gate_reasons.length > 0 && <div className="gate-banner"><span>SAFETY GATE</span><strong>{report.gate_reasons[0]}</strong><small>原始分 {report.raw_score}，高危项不会被平均分掩盖。</small></div>}
      <div className="report-metrics"><div><span>通过率</span><strong>{report.coverage.pass_rate_percent ?? "—"}<small>%</small></strong></div><div><span>波动性</span><strong>{report.coverage.volatility_percent ?? "—"}<small>%</small></strong></div><div><span>用例覆盖</span><strong>{report.coverage.unique_cases}<small> cases</small></strong></div><div><span>完成运行</span><strong>{report.coverage.completed_runs}<small>/{report.coverage.total_runs}</small></strong></div></div>
      <div className="report-grid">
        <section className="dimension-ledger"><header><span>维度得分</span><small>{report.coverage.total_runs} 次确定性运行</small></header>{dimensions.map(([key, label, maximum]) => <div key={key}><span>{label}</span><progress max={maximum} value={report.dimension_scores[key]} /><strong>{report.dimension_scores[key]}<i>/{maximum}</i></strong></div>)}</section>
        <aside className="finding-counts"><span>风险分布</span>{["critical", "high", "medium", "low"].map((severity) => <div key={severity}><b className={`severity-${severity}`}>{severity}</b><strong>{report.finding_counts[severity] ?? 0}</strong></div>)}</aside>
      </div>
      <section className="finding-ledger"><header><div><span className="section-index">TECHNICAL FINDINGS</span><h2>可复现的问题证据</h2></div><div className="report-actions">{!DEMO_MODE && <><a href={`/api/v1/reports/${report.assessment_id}`} download>Canonical JSON</a><a href={`/api/v1/reports/${report.assessment_id}.html`} target="_blank" rel="noreferrer">自包含 HTML</a></>}<button onClick={() => window.print()}>打印 / 另存 PDF</button></div></header>{report.findings.map((finding, index) => <article key={finding.id}><span className="finding-number">F-{String(index + 1).padStart(2, "0")}</span><div><b className={`severity-${finding.severity}`}>{finding.severity}</b><h3>{finding.title}</h3><p>{finding.summary}</p><dl><dt>期望</dt><dd>{finding.expected}</dd><dt>实际</dt><dd>{finding.observed}</dd><dt>证据</dt><dd>{finding.evidence_event_ids.join(", ") || "无事件"}</dd><dt>修复</dt><dd>{finding.remediation}</dd></dl><code>{finding.reproduction}</code></div><aside><span>{finding.case_id}</span><strong>{finding.occurrences}×</strong><small>deterministic</small></aside></article>)}</section>
      <footer className="report-limitations"><strong>适用边界</strong>{report.limitations.map((item) => <p key={item}>— {item}</p>)}</footer>
    </section>
  );
}
