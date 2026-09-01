import { FormEvent, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api, DEMO_MODE } from "../../shared/api";
import { agentLabel, familyLabel } from "../../shared/labels";
import type { Agent, Run, Scenario } from "../../shared/types";

export function TournamentBuilder({ scenarios, agents, onRuns }: { scenarios: Scenario[]; agents: Agent[]; onRuns: (runs: Run[]) => void }) {
  const queryClient = useQueryClient();
  const [selectedScenarios, setSelectedScenarios] = useState<string[]>([]);
  const [selectedAgents, setSelectedAgents] = useState<string[]>([]);
  const [repetitions, setRepetitions] = useState(3);
  const mutation = useMutation({ mutationFn: api.createTournament, onSuccess: async ({ tournament }) => { const result = await api.tournament(tournament.id); onRuns(result.runs); queryClient.invalidateQueries({ queryKey: ["leaderboard"] }); } });
  const submit = (event: FormEvent) => { event.preventDefault(); mutation.mutate({ name: `可靠性对局 · ${new Date().toLocaleDateString("zh-CN")}`, agent_ids: selectedAgents, scenario_ids: selectedScenarios, repetitions }); };
  const runCount = selectedAgents.length * selectedScenarios.length * repetitions;
  return <div className="grid arena-grid">
    <section className="panel hero-panel"><span className="eyebrow">创建一场对局</span><h2>同一关卡，<br />谁先翻车。</h2><p>让不同 Agent 反复进入相同的虚构任务。答案漂亮不算赢，经得住工具调用、异常和恶意输入，才算真的靠谱。</p><div className="score-legend"><span><b>50</b>正确性</span><span><b>25</b>安全守规</span><span><b>15</b>恢复与幂等</span><span><b>10</b>执行效率</span></div></section>
    <form className="panel builder" onSubmit={submit}>
      <fieldset disabled={DEMO_MODE || mutation.isPending}><legend>01 · 选择参赛 Agent</legend><div className="option-grid">{agents.map((agent) => <CheckCard key={agent.id} checked={selectedAgents.includes(agent.id)} label={agentLabel(agent)} meta={`${agent.runtime} · ${agent.id}`} onChange={() => toggle(agent.id, selectedAgents, setSelectedAgents)} />)}</div></fieldset>
      <fieldset disabled={DEMO_MODE || mutation.isPending}><legend>02 · 选择挑战副本</legend><div className="compact-options">{scenarios.map((scenario) => <label key={scenario.id}><input type="checkbox" checked={selectedScenarios.includes(scenario.id)} onChange={() => toggle(scenario.id, selectedScenarios, setSelectedScenarios)} /><span>{scenario.title}</span><small>{familyLabel(scenario.family)}</small></label>)}</div></fieldset>
      <div className="launch-row"><label>重复次数<input type="number" min="1" max="20" value={repetitions} onChange={(event) => setRepetitions(Number(event.target.value))} /></label><div><small>预计运行</small><strong>{runCount}</strong></div><button disabled={DEMO_MODE || !selectedAgents.length || !selectedScenarios.length}>{DEMO_MODE ? "公开演示只读" : mutation.isPending ? "正在开赛…" : "进入竞技场"}</button></div>
      {mutation.error && <div className="alert">创建失败：{mutation.error.message}</div>}
    </form>
  </div>;
}

function CheckCard({ checked, label, meta, onChange }: { checked: boolean; label: string; meta: string; onChange: () => void }) {
  return <label className={`check-card ${checked ? "selected" : ""}`}><input type="checkbox" checked={checked} onChange={onChange} /><span className="agent-icon">◎</span><strong>{label}</strong><small>{meta}</small></label>;
}

function toggle(value: string, values: string[], setValues: (next: string[]) => void) {
  setValues(values.includes(value) ? values.filter((item) => item !== value) : [...values, value]);
}
