import { FormEvent, useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api, DEMO_MODE } from "./api";
import type { Agent, Run, Scenario, TraceEvent } from "./types";

type View = "arena" | "scenarios" | "trace" | "compare" | "leaderboard" | "report";

const views: Array<[View, string]> = [
  ["arena", "发起竞技"],
  ["scenarios", "副本库"],
  ["trace", "运行轨迹"],
  ["compare", "对局对比"],
  ["leaderboard", "竞技榜"],
  ["report", "评测战报"],
];

const familyLabels: Record<string, string> = {
  file: "文件操作",
  sql: "SQL",
  rag: "RAG",
  approval: "人工审批",
  security: "安全攻防",
};

const statusLabels: Record<string, string> = {
  queued: "排队中",
  running: "运行中",
  waiting_approval: "等待审批",
  completed: "已完成",
  failed: "失败",
  cancelled: "已取消",
};

const eventLabels: Record<string, string> = {
  "run.started": "开始挑战",
  "run.completed": "挑战完成",
  "run.failed": "挑战失败",
  "tool.request": "请求工具",
  "tool.result": "工具返回",
  "approval.requested": "等待人工决策",
  "evaluation.completed": "裁判完成评分",
};

function familyLabel(family: string) {
  return familyLabels[family] ?? family;
}

function statusLabel(status: string) {
  return statusLabels[status] ?? status;
}

function agentLabel(agent: Agent) {
  const model = agent.model === "fake-deterministic" ? "确定性假模型" : agent.model;
  if (agent.runtime === "minimal") return `最小工具 Agent · ${model}`;
  if (agent.runtime === "langgraph") return `LangGraph Agent · ${model}`;
  return agent.name;
}

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
        <div className="brand">
          <span className="brand-mark">竞</span>
          <div><strong>Agent 可靠性竞技场</strong><small>RELIABILITY ARENA · v0.1</small></div>
        </div>
        <nav>
          {views.map(([key, label]) => (
            <button key={key} className={view === key ? "active" : ""} onClick={() => setView(key)}>{label}</button>
          ))}
        </nav>
        <div className="mode-badge"><i /> {DEMO_MODE ? "冻结公开演示" : "本地控制台"}</div>
      </aside>
      <main>
        <header className="topbar">
          <div><span className="eyebrow">工具型 AGENT · 可靠性评测</span><h1>{views.find(([key]) => key === view)?.[1]}</h1></div>
          <div className="status-pill">12 个虚构副本</div>
        </header>
        {(scenarios.isError || agents.isError) && <div className="alert">竞技场数据加载失败，请检查本地服务。</div>}
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
    mutation.mutate({ name: `可靠性对局 · ${new Date().toLocaleDateString("zh-CN")}`, agent_ids: selectedAgents, scenario_ids: selectedScenarios, repetitions });
  }
  const runCount = selectedAgents.length * selectedScenarios.length * repetitions;
  return (
    <div className="grid arena-grid">
      <section className="panel hero-panel">
        <span className="eyebrow">创建一场对局</span>
        <h2>同一关卡，<br />谁先翻车。</h2>
        <p>让不同 Agent 反复进入相同的虚构任务。答案漂亮不算赢，经得住工具调用、异常和恶意输入，才算真的靠谱。</p>
        <div className="score-legend"><span><b>50</b>正确性</span><span><b>25</b>安全守规</span><span><b>15</b>恢复与幂等</span><span><b>10</b>执行效率</span></div>
      </section>
      <form className="panel builder" onSubmit={submit}>
        <fieldset disabled={DEMO_MODE || mutation.isPending}>
          <legend>01 · 选择参赛 Agent</legend>
          <div className="option-grid">{agents.map((agent) => <CheckCard key={agent.id} checked={selectedAgents.includes(agent.id)} label={agentLabel(agent)} meta={`${agent.runtime} · ${agent.id}`} onChange={() => toggle(agent.id, selectedAgents, setSelectedAgents)} />)}</div>
        </fieldset>
        <fieldset disabled={DEMO_MODE || mutation.isPending}>
          <legend>02 · 选择挑战副本</legend>
          <div className="compact-options">{scenarios.map((scenario) => <label key={scenario.id}><input type="checkbox" checked={selectedScenarios.includes(scenario.id)} onChange={() => toggle(scenario.id, selectedScenarios, setSelectedScenarios)} /><span>{scenario.title}</span><small>{familyLabel(scenario.family)}</small></label>)}</div>
        </fieldset>
        <div className="launch-row">
          <label>重复次数<input type="number" min="1" max="20" value={repetitions} onChange={(event) => setRepetitions(Number(event.target.value))} /></label>
          <div><small>预计运行</small><strong>{runCount}</strong></div>
          <button disabled={DEMO_MODE || !selectedAgents.length || !selectedScenarios.length}>{DEMO_MODE ? "公开演示只读" : mutation.isPending ? "正在开赛…" : "进入竞技场"}</button>
        </div>
        {mutation.error && <div className="alert">创建失败：{mutation.error.message}</div>}
      </form>
    </div>
  );
}

function CheckCard({ checked, label, meta, onChange }: { checked: boolean; label: string; meta: string; onChange: () => void }) {
  return <label className={`check-card ${checked ? "selected" : ""}`}><input type="checkbox" checked={checked} onChange={onChange} /><span className="agent-icon">◎</span><strong>{label}</strong><small>{meta}</small></label>;
}

function toggle(value: string, values: string[], setValues: (next: string[]) => void) {
  setValues(values.includes(value) ? values.filter((item) => item !== value) : [...values, value]);
}

function ScenarioLibrary({ scenarios }: { scenarios: Scenario[] }) {
  const families = useMemo(() => [...new Set(scenarios.map((scenario) => scenario.family))], [scenarios]);
  return <section className="panel"><div className="section-head"><div><span className="eyebrow">版本化 YAML 场景</span><h2>12 个可重复挑战的副本</h2></div><span>{families.length} 类能力</span></div><div className="scenario-grid">{scenarios.map((scenario, index) => <article key={scenario.id}><div className="scenario-number">{String(index + 1).padStart(2, "0")}</div><span className={`family family-${scenario.family}`}>{familyLabel(scenario.family)}</span><h3>{scenario.title}</h3><p>{scenario.description}</p><footer><code>{scenario.id}@{scenario.version}</code><span>最多 {scenario.max_steps} 步</span></footer></article>)}</div></section>;
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
  const currentStatus = live.data?.run.status ?? run?.status ?? "";
  return <div className="trace-layout"><section className="panel run-summary"><span className="eyebrow">本次运行</span><h2>{run?.id ?? "请先发起一场竞技"}</h2>{run && <><dl><dt>参赛 Agent</dt><dd>{run.agent_id}</dd><dt>挑战副本</dt><dd>{run.scenario_id}</dd><dt>当前状态</dt><dd><span className={`run-status ${currentStatus}`}>{statusLabel(currentStatus)}</span></dd></dl>{approval && !DEMO_MODE && <div className="approval-box"><strong>需要你来做决定</strong><p>{String(approval.payload.reason ?? "检测到敏感工具操作")}</p><button onClick={() => decide.mutate("approve")}>批准并继续</button><button className="danger" onClick={() => decide.mutate("reject")}>拒绝操作</button></div>}<p className="answer">{live.data?.run.answer ?? run.answer}</p></>}</section><section className="panel event-stream"><div className="section-head"><h2>可回放执行轨迹</h2><span>{events.length} 条事件</span></div>{events.length === 0 && <p className="empty-copy">这里还没有轨迹。完成一次挑战后，每次模型思考、工具调用和裁判评分都会按顺序出现。</p>}{events.map((event) => <article key={event.id}><span>{event.sequence}</span><i className={`event-kind ${event.kind}`} /><div><strong>{eventLabels[event.name] ?? event.name}<small className="event-code">{event.name}</small></strong><pre>{JSON.stringify(event.payload, null, 2)}</pre></div></article>)}</section></div>;
}

function ComparePanel({ samples }: { samples: Run[] }) {
  return <section className="panel"><div className="section-head"><div><span className="eyebrow">同场对照</span><h2>两次运行，差在哪里</h2></div></div><div className="compare-grid">{(samples.length ? samples.slice(0, 2) : [null, null]).map((run, index) => <article key={run?.id ?? index}><span>运行 {String(index + 1).padStart(2, "0")}</span><h3>{run?.agent_id ?? "等待已完成的运行"}</h3><dl><dt>挑战副本</dt><dd>{run?.scenario_id ?? "—"}</dd><dt>结果</dt><dd>{run ? statusLabel(run.status) : "—"}</dd><dt>重复轮次</dt><dd>{run?.repetition ?? "—"}</dd></dl><p>{run?.answer ?? "发起竞技后，可以在这里观察两个 Agent 的行为差异。"}</p></article>)}</div></section>;
}

function Leaderboard({ rows }: { rows: Array<{ agent_id: string; mean_score: number; runs: number; min_score: number; max_score: number }> }) {
  return <div className="leader-grid"><section className="panel"><div className="section-head"><div><span className="eyebrow">确定性核心评分</span><h2>谁更稳定，分数说话</h2></div></div><table><thead><tr><th>排名</th><th>Agent</th><th>平均分</th><th>运行次数</th><th>得分区间</th></tr></thead><tbody>{rows.map((row, index) => <tr key={row.agent_id}><td>{index + 1}</td><td>{row.agent_id}</td><td><strong>{row.mean_score}</strong></td><td>{row.runs}</td><td>{row.min_score}–{row.max_score}</td></tr>)}</tbody></table></section><section className="panel chart-panel"><ResponsiveContainer width="100%" height={340}><BarChart data={rows}><CartesianGrid strokeDasharray="3 3" stroke="#233049" /><XAxis dataKey="agent_id" stroke="#8190a9" /><YAxis domain={[0, 100]} stroke="#8190a9" /><Tooltip /><Bar dataKey="mean_score" name="平均分" fill="#58e0b7" radius={[6, 6, 0, 0]} /></BarChart></ResponsiveContainer></section></div>;
}

function ReportSummary({ scenarios, agents }: { scenarios: Scenario[]; agents: Agent[] }) {
  return <section className="panel report"><span className="eyebrow">冻结评测战报</span><h2>可靠性不是一张截图，<br />而是一段分布。</h2><div className="metric-row"><div><strong>{scenarios.length}</strong><span>挑战副本</span></div><div><strong>{agents.length}</strong><span>Agent 配置</span></div><div><strong>3×</strong><span>默认重复运行</span></div><div><strong>100</strong><span>核心总分</span></div></div><p>公开战报只包含虚构场景、脱敏后的聚合轨迹和评测分数。原始提示词、凭证、本地数据库以及私有模型请求，都不会进入演示包。</p></section>;
}
