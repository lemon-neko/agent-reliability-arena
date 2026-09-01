import { useEffect, useMemo, useState } from "react";
import { api } from "../../shared/api";
import type { AgentTarget, Finding, RiskCase, RiskReport } from "../../shared/types";

type DemoPhase = "ready" | "running" | "complete";

const triggerPoints = [11, 29, 48, 63];

export function RiskAuditDemo({
  targets,
  cases,
  onReport,
}: {
  targets: AgentTarget[];
  cases: RiskCase[];
  onReport: (report: RiskReport) => void;
}) {
  const [targetId, setTargetId] = useState(targets[0]?.id ?? "demo-vulnerable");
  const [phase, setPhase] = useState<DemoPhase>("ready");
  const [completed, setCompleted] = useState(0);
  const [report, setReport] = useState<RiskReport | null>(null);
  const visibleFindings = useMemo(
    () => report?.findings.slice(0, triggerPoints.filter((point) => completed >= point).length) ?? [],
    [completed, report],
  );

  useEffect(() => {
    if (phase !== "running") return;
    if (completed >= 72) {
      setPhase("complete");
      return;
    }
    const timer = window.setTimeout(
      () => setCompleted((value) => Math.min(72, value + (value < 12 ? 1 : 2))),
      72,
    );
    return () => window.clearTimeout(timer);
  }, [completed, phase]);

  const start = async () => {
    const next = await api.demoReport(targetId);
    setReport(next);
    setCompleted(0);
    setPhase("running");
  };

  const selectTarget = (value: string) => {
    setTargetId(value);
    setPhase("ready");
    setCompleted(0);
    setReport(null);
  };

  const activeCase = cases[Math.min(cases.length - 1, Math.floor(completed / 6))];
  return (
    <section className="audit-demo" data-phase={phase}>
      <header className="page-heading compact">
        <div><span className="section-index">LIVE DETERMINISTIC DEMO</span><h1>发起风险体检</h1><p>公开页面只播放浏览器内确定性剧本；不会调用 Endpoint，也不会发送写请求。</p></div>
        <span className="demo-disclosure">DEMO DATA · 2026-09-01</span>
      </header>

      <div className="audit-stage">
        <aside className="audit-config">
          <div className="config-step"><span>01</span><label>被测 Agent<select value={targetId} onChange={(event) => selectTarget(event.target.value)} disabled={phase === "running"}>{targets.map((item) => <option key={item.id} value={item.id}>{item.name} · {item.version}</option>)}</select></label></div>
          <div className="config-step"><span>02</span><div><small>测试档位</small><strong>Standard</strong><p>36 个逻辑用例 × 2 次重复</p></div></div>
          <div className="config-step"><span>03</span><div><small>执行预算</small><strong>72 runs / 4 workers</strong><p>固定 Seed · 20260901</p></div></div>
          {phase !== "running" && <button className="audit-launch" onClick={start}><span>{phase === "complete" ? "重新执行" : "执行 72 项测试"}</span><small>约 6 秒浏览器回放</small></button>}
        </aside>

        <div className="audit-console">
          <div className="console-status">
            <div><span className={`status-light ${phase}`} /><small>{phase === "ready" ? "READY" : phase === "running" ? "RUNNING" : "REPORT READY"}</small></div>
            <strong>{String(completed).padStart(2, "0")}<i>/72</i></strong>
          </div>
          <progress max={72} value={completed} aria-label="评测运行进度" />
          <div className="run-matrix" aria-live="polite">
            {Array.from({ length: 72 }, (_, index) => {
              const done = index < completed;
              const failed = targetId === "demo-vulnerable" && triggerPoints.includes(index + 1) && done;
              return <i key={index} className={failed ? "failed" : done ? "passed" : "pending"} title={`Run ${index + 1}`} />;
            })}
          </div>
          <div className="live-readout">
            <div><span>当前用例</span><strong>{phase === "ready" ? "等待启动" : activeCase?.title ?? "正在汇总报告"}</strong><code>{activeCase?.id ?? "tool-agent-baseline/1.0.0"}</code></div>
            <div><span>最新证据</span><strong>{visibleFindings.at(-1)?.title ?? (completed ? "工具调用符合策略" : "尚无运行事件")}</strong><code>{visibleFindings.length ? `${visibleFindings.at(-1)?.severity} · deterministic` : "trace pending"}</code></div>
          </div>
          <FindingTicker findings={visibleFindings} />
          {phase === "complete" && report && (
            <div className="audit-outcome">
              <div><span>最终等级</span><strong>{report.grade}</strong></div>
              <div><span>可靠性分</span><strong>{report.final_score}</strong></div>
              <p>{report.verdict === "ready" ? "未触发 High / Critical 门禁" : report.gate_reasons[0]}</p>
              <button onClick={() => onReport(report)}>打开完整风险报告 →</button>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}

function FindingTicker({ findings }: { findings: Finding[] }) {
  return (
    <div className="finding-ticker">
      <header><span>实时 Finding</span><small>{findings.length ? `${findings.length} 条已归档` : "策略引擎监听中"}</small></header>
      {findings.slice(-3).map((finding) => <article key={finding.id}><b className={`severity-${finding.severity}`}>{finding.severity}</b><div><strong>{finding.title}</strong><small>{finding.case_id} · 证据已脱敏</small></div></article>)}
      {!findings.length && <p>当 Agent 越过权限、审批或数据边界时，确定性证据会出现在这里。</p>}
    </div>
  );
}
