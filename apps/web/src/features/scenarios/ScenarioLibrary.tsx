import { useMemo } from "react";
import { familyLabel } from "../../shared/labels";
import type { Scenario } from "../../shared/types";

export function ScenarioLibrary({ scenarios }: { scenarios: Scenario[] }) {
  const families = useMemo(() => [...new Set(scenarios.map((scenario) => scenario.family))], [scenarios]);
  return <section className="panel"><div className="section-head"><div><span className="eyebrow">版本化 YAML 场景</span><h2>12 个可重复挑战的副本</h2></div><span>{families.length} 类能力</span></div><div className="scenario-grid">{scenarios.map((scenario, index) => <article key={scenario.id}><div className="scenario-number">{String(index + 1).padStart(2, "0")}</div><span className={`family family-${scenario.family}`}>{familyLabel(scenario.family)}</span><h3>{scenario.title}</h3><p>{scenario.description}</p><footer><code>{scenario.id}@{scenario.version}</code><span>最多 {scenario.max_steps} 步</span></footer></article>)}</div></section>;
}
