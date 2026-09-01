import { useEffect, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { api, DEMO_MODE } from "../../shared/api";
import { statusLabel } from "../../shared/labels";
import type { Run, TraceEvent } from "../../shared/types";

const eventLabels: Record<string, string> = {
  "run.started": "开始挑战",
  "run.completed": "挑战完成",
  "run.failed": "挑战失败",
  "tool.request": "请求工具",
  "tool.result": "工具返回",
  "model.response": "Agent 作出判断",
  "policy.blocked": "安全策略阻断",
  "approval.requested": "等待人工决策",
  "approval.decided": "记录人类决定",
  "evaluation.completed": "裁判完成评分",
};

export function TracePanel({ run, frozenEvents }: { run: Run | null; frozenEvents: TraceEvent[] }) {
  const live = useQuery({
    queryKey: ["run", run?.id],
    queryFn: () => api.run(run!.id),
    enabled: Boolean(run && !DEMO_MODE),
    refetchInterval: 1000,
  });
  const [streamed, setStreamed] = useState<TraceEvent[]>([]);
  const runId = run?.id;
  useEffect(() => {
    setStreamed([]);
    if (!runId || DEMO_MODE) return;
    const source = new EventSource(`/api/runs/${runId}/events`);
    const receive = (event: MessageEvent) => {
      const next = JSON.parse(event.data) as TraceEvent;
      setStreamed((current) => current.some((item) => item.id === next.id) ? current : [...current, next]);
    };
    ["run", "model", "tool", "approval", "retry", "error", "evaluation"].forEach((kind) => source.addEventListener(kind, receive));
    source.addEventListener("end", () => source.close());
    source.onerror = () => source.close();
    return () => source.close();
  }, [runId]);
  const events = DEMO_MODE ? frozenEvents : streamed.length ? streamed : live.data?.events ?? [];
  const approval = events.find((event) => event.name === "approval.requested");
  const decide = useMutation({ mutationFn: (decision: "approve" | "reject") => api.decideApproval(run!.id, String(approval?.payload.id), decision) });
  const currentStatus = live.data?.run.status ?? run?.status ?? "";
  return <div className="trace-layout">
    <section className="panel run-summary">
      <span className="eyebrow">本次运行</span><h2>{run?.id ?? "请先发起一场竞技"}</h2>
      {run && <><dl><dt>参赛 Agent</dt><dd>{run.agent_id}</dd><dt>挑战副本</dt><dd>{run.scenario_id}</dd><dt>当前状态</dt><dd><span className={`run-status ${currentStatus}`}>{statusLabel(currentStatus)}</span></dd></dl>
        {approval && !DEMO_MODE && <div className="approval-box"><strong>需要你来做决定</strong><p>{String(approval.payload.reason ?? "检测到敏感工具操作")}</p><button onClick={() => decide.mutate("approve")}>批准并继续</button><button className="danger" onClick={() => decide.mutate("reject")}>拒绝操作</button></div>}
        <p className="answer">{live.data?.run.answer ?? run.answer}</p></>}
    </section>
    <section className="panel event-stream"><div className="section-head"><h2>可回放执行轨迹</h2><span>{events.length} 条事件</span></div>
      {events.length === 0 && <p className="empty-copy">这里还没有轨迹。完成一次挑战后，每次模型思考、工具调用和裁判评分都会按顺序出现。</p>}
      {events.map((event) => <article key={event.id}><span>{event.sequence}</span><i className={`event-kind ${event.kind}`} /><div><strong>{eventLabels[event.name] ?? event.name}<small className="event-code">{event.name}</small></strong><pre>{JSON.stringify(event.payload, null, 2)}</pre></div></article>)}
    </section>
  </div>;
}

export function ComparePanel({ samples }: { samples: Run[] }) {
  return <section className="panel"><div className="section-head"><div><span className="eyebrow">同场对照</span><h2>两次运行，差在哪里</h2></div></div><div className="compare-grid">{(samples.length ? samples.slice(0, 2) : [null, null]).map((run, index) => <article key={run?.id ?? index}><span>运行 {String(index + 1).padStart(2, "0")}</span><h3>{run?.agent_id ?? "等待已完成的运行"}</h3><dl><dt>挑战副本</dt><dd>{run?.scenario_id ?? "—"}</dd><dt>结果</dt><dd>{run ? statusLabel(run.status) : "—"}</dd><dt>重复轮次</dt><dd>{run?.repetition ?? "—"}</dd></dl><p>{run?.answer ?? "发起竞技后，可以在这里观察两个 Agent 的行为差异。"}</p></article>)}</div></section>;
}
