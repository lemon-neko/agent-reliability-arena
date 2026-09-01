import type { Agent, Scenario } from "../../shared/types";

export function ReportSummary({ scenarios, agents }: { scenarios: Scenario[]; agents: Agent[] }) {
  return <section className="panel report"><span className="eyebrow">公开评测战报</span><h2>可靠性不是一张截图，<br />而是一段分布。</h2><div className="metric-row"><div><strong>{scenarios.length}</strong><span>挑战副本</span></div><div><strong>{agents.length}</strong><span>Agent 配置</span></div><div><strong>3×</strong><span>默认重复运行</span></div><div><strong>100</strong><span>核心总分</span></div></div><p>公开战报只包含虚构场景、脱敏后的聚合轨迹和评测分数。原始提示词、凭证、本地数据库以及私有模型请求，都不会进入演示包。</p></section>;
}
