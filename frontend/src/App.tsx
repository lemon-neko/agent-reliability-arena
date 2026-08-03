import { FormEvent, useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api, DEMO_MODE } from "./api";
import type { Agent, Run, Scenario, TraceEvent } from "./types";

type View = "arena" | "scenarios" | "trace" | "compare" | "leaderboard" | "report";

const views: Array<[View, string]> = [
  ["arena", "New tournament"],
  ["scenarios", "Scenario library"],
  ["trace", "Live trace"],
  ["compare", "Run compare"],
  ["leaderboard", "Leaderboard"],
  ["report", "Report"],
];

export default function App() {
  const [view, setView] = useState<View>("arena");
  const [selectedRun, setSelectedRun] = useState<Run | null>(null);
  const scenarios = useQuery({ queryKey: ["scenarios"], queryFn: api.scenarios });
  const agents = useQuery({ queryKey: ["agents"], queryFn: api.agents });
  const board = useQuery({ queryKey: ["leaderboard"], queryFn: api.leaderboard });
  const samples = useQuery({ queryKey: ["samples"], queryFn: api.sampleRuns });

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand"><span className="brand-mark">A</span><div><strong>Agent Reliability</strong><small>ARENA · v0.1</small></div></div>
        <nav>{views.map(([key, label]) => <button key={key} className={view === key ? "active" : ""} onClick={() => setView(key)}>{label}</button>)}</nav>
        <div className="mode-badge"><i /> {DEMO_MODE ? "Frozen public demo" : "Local control plane"}</div>
      </aside>
      <main>
        <header className="topbar"><div><span className="eyebrow">TOOL-USE RELIABILITY</span><h1>{views.find(([key]) => key === view)?.[1]}</h1></div><div className="status-pill">12 synthetic dungeons</div></header>
        {(scenarios.isError || agents.isError) && <div className="alert">Unable to load arena data.</div>}
        {view === "arena" && <TournamentBuilder scenarios={scenarios.data ?? []} agents={agents.data ?? []} onRuns={(runs) => { setSelectedRun(runs[0] ?? null); setView("trace"); }} />}
        {view === "scenarios" && <ScenarioLibrary scenarios={scenarios.data ?? []} />}
        {view === "trace" && <TracePanel run={selectedRun ?? samples.data?.[0]?.run ?? null} frozenEvents={samples.data?.[0]?.events ?? []} />}
        {view === "compare" && <ComparePanel samples={samples.data?.map((sample) => sample.run) ?? []} />}
        {view === "leaderboard" && <Leaderboard rows={board.data ?? []} />}
        {view === "report" && <ReportSummary scenarios={scenarios.data ?? []} agents={agents.data ?? []} />}
      </main>
    </div>
  );
}

function TournamentBuilder({ scenarios, agents, onRuns }: { scenarios: Scenario[]; agents: Agent[]; onRuns: (runs: Run[]) => void }) {
  const queryClient = useQueryClient();
  const [selectedScenarios, setSelectedScenarios] = useState<string[]>([]);
  const [selectedAgents, setSelectedAgents] = useState<string[]>([]);
  const [repetitions, setRepetitions] = useState(3);
  const mutation = useMutation({
    mutationFn: api.createTournament,
    onSuccess: async ({ tournament }) => {
      const result = await api.tournament(tournament.id);
      onRuns(result.runs);
      queryClient.invalidateQueries({ queryKey: ["leaderboard"] });
    },
  });
  function submit(event: FormEvent) {
    event.preventDefault();
    mutation.mutate({ name: `Arena match · ${new Date().toLocaleDateString()}`, agent_ids: selectedAgents, scenario_ids: selectedScenarios, repetitions });
  }
  const runCount = selectedAgents.length * selectedScenarios.length * repetitions;
  return <div className="grid arena-grid"><section className="panel hero-panel"><span className="eyebrow">CREATE MATCH</span><h2>Same dungeon.<br/>Different minds.</h2><p>Repeat identical synthetic tasks and compare what survives contact with tools, failures, and hostile input.</p><div className="score-legend"><span><b>50</b> Correct</span><span><b>25</b> Safe</span><span><b>15</b> Recover</span><span><b>10</b> Efficient</span></div></section><form className="panel builder" onSubmit={submit}><fieldset disabled={DEMO_MODE || mutation.isPending}><legend>1 · Choose runtimes</legend><div className="option-grid">{agents.map((agent) => <CheckCard key={agent.id} checked={selectedAgents.includes(agent.id)} label={agent.name} meta={`${agent.runtime} · ${agent.model}`} onChange={() => toggle(agent.id, selectedAgents, setSelectedAgents)} />)}</div></fieldset><fieldset disabled={DEMO_MODE || mutation.isPending}><legend>2 · Choose dungeons</legend><div className="compact-options">{scenarios.map((scenario) => <label key={scenario.id}><input type="checkbox" checked={selectedScenarios.includes(scenario.id)} onChange={() => toggle(scenario.id, selectedScenarios, setSelectedScenarios)} /><span>{scenario.title}</span><small>{scenario.family}</small></label>)}</div></fieldset><div className="launch-row"><label>Repetitions<input type="number" min="1" max="20" value={repetitions} onChange={(event) => setRepetitions(Number(event.target.value))} /></label><div><small>RUN MATRIX</small><strong>{runCount}</strong></div><button disabled={DEMO_MODE || !selectedAgents.length || !selectedScenarios.length}>{DEMO_MODE ? "Read-only demo" : mutation.isPending ? "Launching…" : "Launch tournament"}</button></div>{mutation.error && <div className="alert">{mutation.error.message}</div>}</form></div>;
}

function CheckCard({ checked, label, meta, onChange }: { checked: boolean; label: string; meta: string; onChange: () => void }) { return <label className={`check-card ${checked ? "selected" : ""}`}><input type="checkbox" checked={checked} onChange={onChange} /><span className="agent-icon">◎</span><strong>{label}</strong><small>{meta}</small></label>; }
function toggle(value: string, values: string[], setValues: (next: string[]) => void) { setValues(values.includes(value) ? values.filter((item) => item !== value) : [...values, value]); }

function ScenarioLibrary({ scenarios }: { scenarios: Scenario[] }) {
  const families = useMemo(() => [...new Set(scenarios.map((scenario) => scenario.family))], [scenarios]);
  return <section className="panel"><div className="section-head"><div><span className="eyebrow">VERSIONED YAML</span><h2>12 reproducible dungeons</h2></div><span>{families.length} families</span></div><div className="scenario-grid">{scenarios.map((scenario, index) => <article key={scenario.id}><div className="scenario-number">{String(index + 1).padStart(2, "0")}</div><span className={`family family-${scenario.family}`}>{scenario.family}</span><h3>{scenario.title}</h3><p>{scenario.description}</p><footer><code>{scenario.id}@{scenario.version}</code><span>{scenario.max_steps} max steps</span></footer></article>)}</div></section>;
}

function TracePanel({ run, frozenEvents }: { run: Run | null; frozenEvents: TraceEvent[] }) {
  const live = useQuery({ queryKey: ["run", run?.id], queryFn: () => api.run(run!.id), enabled: Boolean(run && !DEMO_MODE), refetchInterval: 1000 });
  const [streamed, setStreamed] = useState<TraceEvent[]>([]);
  useEffect(() => {
    setStreamed([]);
    if (!run || DEMO_MODE) return;
    const source = new EventSource(`/api/runs/${run.id}/events`);
    const receive = (event: MessageEvent) => {
      const next = JSON.parse(event.data) as TraceEvent;
      setStreamed((current) => current.some((item) => item.id === next.id) ? current : [...current, next]);
    };
    ["run", "model", "tool", "approval", "retry", "error", "evaluation"].forEach((kind) => source.addEventListener(kind, receive));
    source.addEventListener("end", () => source.close());
    source.onerror = () => source.close();
    return () => source.close();
  }, [run?.id]);
  const events = DEMO_MODE ? frozenEvents : streamed.length ? streamed : live.data?.events ?? [];
  const approval = events.find((event) => event.name === "approval.requested");
  const decide = useMutation({ mutationFn: (decision: "approve" | "reject") => api.decideApproval(run!.id, String(approval?.payload.id), decision) });
  return <div className="trace-layout"><section className="panel run-summary"><span className="eyebrow">RUN</span><h2>{run?.id ?? "Select a run"}</h2>{run && <><dl><dt>Agent</dt><dd>{run.agent_id}</dd><dt>Scenario</dt><dd>{run.scenario_id}</dd><dt>Status</dt><dd><span className={`run-status ${live.data?.run.status ?? run.status}`}>{live.data?.run.status ?? run.status}</span></dd></dl>{approval && !DEMO_MODE && <div className="approval-box"><strong>Human decision required</strong><p>{String(approval.payload.reason ?? "Sensitive tool action")}</p><button onClick={() => decide.mutate("approve")}>Approve and resume</button><button className="danger" onClick={() => decide.mutate("reject")}>Reject</button></div>}<p className="answer">{live.data?.run.answer ?? run.answer}</p></>}</section><section className="panel event-stream"><div className="section-head"><h2>Replayable trace</h2><span>{events.length} events</span></div>{events.map((event) => <article key={event.id}><span>{event.sequence}</span><i className={`event-kind ${event.kind}`} /><div><strong>{event.name}</strong><pre>{JSON.stringify(event.payload, null, 2)}</pre></div></article>)}</section></div>;
}

function ComparePanel({ samples }: { samples: Run[] }) { return <section className="panel"><div className="section-head"><div><span className="eyebrow">SIDE BY SIDE</span><h2>Run comparison</h2></div></div><div className="compare-grid">{(samples.length ? samples.slice(0, 2) : [null, null]).map((run, index) => <article key={run?.id ?? index}><span>RUN {index + 1}</span><h3>{run?.agent_id ?? "Choose a completed run"}</h3><dl><dt>Scenario</dt><dd>{run?.scenario_id ?? "—"}</dd><dt>Status</dt><dd>{run?.status ?? "—"}</dd><dt>Repetition</dt><dd>{run?.repetition ?? "—"}</dd></dl><p>{run?.answer ?? "Local runs become available after a tournament."}</p></article>)}</div></section>; }

function Leaderboard({ rows }: { rows: Array<{ agent_id: string; mean_score: number; runs: number; min_score: number; max_score: number }> }) { return <div className="leader-grid"><section className="panel"><div className="section-head"><div><span className="eyebrow">DETERMINISTIC CORE</span><h2>Leaderboard</h2></div></div><table><thead><tr><th>#</th><th>Agent</th><th>Mean</th><th>Runs</th><th>Range</th></tr></thead><tbody>{rows.map((row, index) => <tr key={row.agent_id}><td>{index + 1}</td><td>{row.agent_id}</td><td><strong>{row.mean_score}</strong></td><td>{row.runs}</td><td>{row.min_score}–{row.max_score}</td></tr>)}</tbody></table></section><section className="panel chart-panel"><ResponsiveContainer width="100%" height={340}><BarChart data={rows}><CartesianGrid strokeDasharray="3 3" stroke="#233049"/><XAxis dataKey="agent_id" stroke="#8190a9"/><YAxis domain={[0, 100]} stroke="#8190a9"/><Tooltip/><Bar dataKey="mean_score" fill="#58e0b7" radius={[6,6,0,0]}/></BarChart></ResponsiveContainer></section></div>; }

function ReportSummary({ scenarios, agents }: { scenarios: Scenario[]; agents: Agent[] }) { return <section className="panel report"><span className="eyebrow">FROZEN MATCH REPORT</span><h2>Reliability is a distribution,<br/>not a screenshot.</h2><div className="metric-row"><div><strong>{scenarios.length}</strong><span>Scenarios</span></div><div><strong>{agents.length}</strong><span>Agent profiles</span></div><div><strong>3×</strong><span>Default repeats</span></div><div><strong>100</strong><span>Core points</span></div></div><p>The public report contains synthetic scenario metadata and sanitized aggregate traces only. Raw prompts, credentials, local databases, and private model payloads never enter the demo bundle.</p></section>; }
