import type { Agent, Run, Scenario, TraceEvent } from "../../shared/types";
import { InteractiveDemo } from "../demo/InteractiveDemo";
import { ScenarioLibrary } from "../scenarios/ScenarioLibrary";
import { TournamentBuilder } from "../tournament/TournamentBuilder";
import { DEMO_MODE } from "../../shared/api";

export function ArenaWorkspace({
  scenarios,
  agents,
  onRuns,
  onInspect,
}: {
  scenarios: Scenario[];
  agents: Agent[];
  onRuns: (runs: Run[]) => void;
  onInspect: (payload: { run: Run; events: TraceEvent[] }) => void;
}) {
  return <section className="workspace-page arena-workspace"><header className="page-heading"><div><span className="section-index">LEGACY ARENA</span><h1>多 Agent 竞技场</h1><p>比较 Runtime 和模型配置的原有能力继续保留，风险体检是新的主流程。</p></div></header>{DEMO_MODE ? <InteractiveDemo onInspect={onInspect} /> : <TournamentBuilder scenarios={scenarios} agents={agents} onRuns={onRuns} />}<ScenarioLibrary scenarios={scenarios} /></section>;
}
