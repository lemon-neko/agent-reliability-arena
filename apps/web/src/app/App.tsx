import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { InteractiveDemo } from "../features/demo/InteractiveDemo";
import { Leaderboard } from "../features/leaderboard/Leaderboard";
import { ReportSummary } from "../features/report/ReportSummary";
import { ScenarioLibrary } from "../features/scenarios/ScenarioLibrary";
import { ComparePanel, TracePanel } from "../features/trace/TracePanels";
import { TournamentBuilder } from "../features/tournament/TournamentBuilder";
import { api, DEMO_MODE } from "../shared/api";
import type { Run, TraceEvent } from "../shared/types";

type View = "arena" | "scenarios" | "trace" | "compare" | "leaderboard" | "report";

const views: Array<[View, string]> = [
  ["arena", "发起竞技"], ["scenarios", "副本库"], ["trace", "运行轨迹"],
  ["compare", "对局对比"], ["leaderboard", "竞技榜"], ["report", "评测战报"],
];

export default function App() {
  const [view, setView] = useState<View>("arena");
  const [selectedRun, setSelectedRun] = useState<Run | null>(null);
  const [selectedDemoEvents, setSelectedDemoEvents] = useState<TraceEvent[] | null>(null);
  const scenarios = useQuery({ queryKey: ["scenarios"], queryFn: api.scenarios });
  const agents = useQuery({ queryKey: ["agents"], queryFn: api.agents });
  const board = useQuery({ queryKey: ["leaderboard"], queryFn: api.leaderboard });
  const samples = useQuery({ queryKey: ["samples"], queryFn: api.sampleRuns });

  return <div className="app-shell">
    <aside className="sidebar">
      <div className="brand"><span className="brand-mark">竞</span><div><strong>Agent 可靠性竞技场</strong><small>RELIABILITY ARENA · v0.1</small></div></div>
      <nav>{views.map(([key, label]) => <button key={key} className={view === key ? "active" : ""} onClick={() => setView(key)}>{label}</button>)}</nav>
      <div className="mode-badge"><i /> {DEMO_MODE ? "交互式公开演示" : "本地控制台"}</div>
    </aside>
    <main>
      <header className="topbar"><div><span className="eyebrow">工具型 AGENT · 可靠性评测</span><h1>{views.find(([key]) => key === view)?.[1]}</h1></div><div className="status-pill">{DEMO_MODE ? "无需 API · 浏览器内运行" : "12 个虚构副本"}</div></header>
      {(scenarios.isError || agents.isError) && <div className="alert">竞技场数据加载失败，请检查本地服务。</div>}
      {view === "arena" && (DEMO_MODE
        ? <InteractiveDemo onInspect={({ run, events }) => { setSelectedRun(run); setSelectedDemoEvents(events); setView("trace"); }} />
        : <TournamentBuilder scenarios={scenarios.data ?? []} agents={agents.data ?? []} onRuns={(runs) => { setSelectedRun(runs[0] ?? null); setSelectedDemoEvents(null); setView("trace"); }} />)}
      {view === "scenarios" && <ScenarioLibrary scenarios={scenarios.data ?? []} />}
      {view === "trace" && <TracePanel run={selectedRun ?? samples.data?.[0]?.run ?? null} frozenEvents={selectedDemoEvents ?? samples.data?.[0]?.events ?? []} />}
      {view === "compare" && <ComparePanel samples={samples.data?.map((sample) => sample.run) ?? []} />}
      {view === "leaderboard" && <Leaderboard rows={board.data ?? []} />}
      {view === "report" && <ReportSummary scenarios={scenarios.data ?? []} agents={agents.data ?? []} />}
    </main>
  </div>;
}
