import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ArenaWorkspace } from "../features/arena/ArenaWorkspace";
import { AssessmentBuilder } from "../features/assessment/AssessmentBuilder";
import { ExecutionCenter } from "../features/assessment/ExecutionCenter";
import { RiskAuditDemo } from "../features/assessment/RiskAuditDemo";
import { PublicBenchmark } from "../features/leaderboard/PublicBenchmark";
import { RiskOverview } from "../features/overview/RiskOverview";
import { RiskReportView } from "../features/report/RiskReportView";
import { AgentProjects } from "../features/targets/AgentProjects";
import { TracePanel } from "../features/trace/TracePanels";
import { api, DEMO_MODE } from "../shared/api";
import type { AssessmentDetail, RiskReport, Run, TraceEvent } from "../shared/types";

type View = "overview" | "targets" | "audit" | "execution" | "reports" | "benchmark" | "arena";

const views: Array<[View, string, string]> = [
  ["overview", "项目总览", "01"],
  ["targets", "Agent 项目", "02"],
  ["audit", "新建体检", "03"],
  ["execution", "执行中心", "04"],
  ["reports", "风险报告", "05"],
  ["benchmark", "公开基准", "06"],
  ["arena", "竞技场", "07"],
];

export default function App() {
  const [view, setView] = useState<View>(DEMO_MODE ? "audit" : "overview");
  const [assessment, setAssessment] = useState<AssessmentDetail | null>(null);
  const [report, setReport] = useState<RiskReport | null>(null);
  const [selectedRun, setSelectedRun] = useState<Run | null>(null);
  const [selectedDemoEvents, setSelectedDemoEvents] = useState<TraceEvent[]>([]);

  const riskCases = useQuery({ queryKey: ["risk-cases"], queryFn: api.riskCases });
  const targets = useQuery({ queryKey: ["risk-targets"], queryFn: api.agentTargets });
  const assessments = useQuery({ queryKey: ["risk-assessments"], queryFn: api.assessments });
  const publicBoard = useQuery({ queryKey: ["public-leaderboard"], queryFn: api.publicLeaderboard });
  const scenarios = useQuery({ queryKey: ["scenarios"], queryFn: api.scenarios });
  const agents = useQuery({ queryKey: ["agents"], queryFn: api.agents });

  const openReport = (next: RiskReport) => {
    setReport(next);
    setView("reports");
  };
  const updateAssessment = (detail: AssessmentDetail) => {
    setAssessment(detail);
    if (detail.report) setReport(detail.report);
    setView(detail.report ? "reports" : "execution");
  };
  const hasError = [riskCases, targets, publicBoard].some((query) => query.isError);

  return (
    <div className="product-shell">
      <a className="skip-link" href="#main-content">跳到主要内容</a>
      <header className="product-header">
        <button className="wordmark" onClick={() => setView("overview")} aria-label="返回项目总览">
          <span>AR</span><div><strong>Agent Reliability Arena</strong><small>风险体检与公开基准 · v0.2</small></div>
        </button>
        <nav aria-label="主导航">
          {views.map(([key, label, index]) => (
            <button key={key} className={view === key ? "active" : ""} onClick={() => setView(key)}>
              <small>{index}</small>{label}
            </button>
          ))}
        </nav>
        <div className="environment-mark"><i /><span>{DEMO_MODE ? "公开演示" : "本地私有"}</span></div>
      </header>

      <main id="main-content">
        {hasError && <div className="global-error">控制面数据加载失败。请确认本地 API 已启动，或刷新公开 Demo。</div>}
        {view === "overview" && <RiskOverview cases={riskCases.data ?? []} targets={targets.data ?? []} assessments={assessments.data ?? []} leaderboard={publicBoard.data ?? []} onNavigate={setView} />}
        {view === "targets" && <AgentProjects targets={targets.data ?? []} />}
        {view === "audit" && (DEMO_MODE
          ? <RiskAuditDemo targets={targets.data ?? []} cases={riskCases.data ?? []} onReport={openReport} />
          : <AssessmentBuilder targets={targets.data ?? []} cases={riskCases.data ?? []} onAssessment={updateAssessment} />)}
        {view === "execution" && <ExecutionCenter detail={assessment} onCancelled={updateAssessment} />}
        {view === "reports" && <RiskReportView report={report} />}
        {view === "benchmark" && <PublicBenchmark entries={publicBoard.data ?? []} />}
        {view === "arena" && <>
          <ArenaWorkspace
            scenarios={scenarios.data ?? []}
            agents={agents.data ?? []}
            onRuns={(runs) => { setSelectedRun(runs[0] ?? null); setSelectedDemoEvents([]); }}
            onInspect={({ run, events }) => { setSelectedRun(run); setSelectedDemoEvents(events); }}
          />
          {selectedRun && <div className="legacy-trace"><TracePanel run={selectedRun} frozenEvents={selectedDemoEvents} /></div>}
        </>}
      </main>

      <footer className="product-footer">
        <span>Agent Reliability Arena · MIT</span>
        <p>本地评测默认不上传 Endpoint、凭证、Prompt 或原始 Trace。</p>
        <a href="https://github.com/lemon-neko/agent-reliability-arena" target="_blank" rel="noreferrer">源码与方法说明 ↗</a>
      </footer>
    </div>
  );
}
