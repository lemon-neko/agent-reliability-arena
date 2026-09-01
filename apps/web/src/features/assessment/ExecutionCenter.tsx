import { useMutation } from "@tanstack/react-query";
import { api } from "../../shared/api";
import type { AssessmentDetail } from "../../shared/types";

export function ExecutionCenter({ detail, onCancelled }: { detail: AssessmentDetail | null; onCancelled: (detail: AssessmentDetail) => void }) {
  const cancel = useMutation({
    mutationFn: async (assessmentId: string) => {
      await api.cancelAssessment(assessmentId);
      return api.assessment(assessmentId);
    },
    onSuccess: onCancelled,
  });
  if (!detail) return <section className="workspace-page"><header className="page-heading"><div><span className="section-index">EXECUTION CENTER</span><h1>执行中心</h1><p>发起体检后，这里会展示并发运行、失败隔离和测试状态。</p></div></header><div className="empty-state large"><b>∷</b><h2>还没有活动评测</h2><p>从“新建体检”选择 Agent 和测试档位。</p></div></section>;
  const { assessment, runs } = detail;
  const failed = runs.filter((run) => ["failed", "timed_out"].includes(run.status)).length;
  return (
    <section className="workspace-page">
      <header className="page-heading"><div><span className="section-index">EXECUTION CENTER</span><h1>{assessment.name}</h1><p>{assessment.suite_version} · {assessment.profile} · Seed {assessment.seed}</p></div><div className="execution-actions"><span className={`run-state ${assessment.status}`}>{assessment.status}</span>{["queued", "running"].includes(assessment.status) && <button onClick={() => cancel.mutate(assessment.id)} disabled={cancel.isPending}>{cancel.isPending ? "正在取消…" : "取消剩余测试"}</button>}</div></header>
      <div className="execution-summary"><div><span>进度</span><strong>{assessment.completed_runs}/{assessment.total_runs}</strong></div><div><span>失败隔离</span><strong>{failed}</strong></div><div><span>并发</span><strong>{assessment.concurrency}</strong></div><progress max={assessment.total_runs} value={assessment.completed_runs} /></div>
      <div className="execution-table"><header><span>Test run</span><span>Variant</span><span>Tools</span><span>Duration</span><span>Status</span></header>{runs.slice(-24).map((run) => <article key={run.id}><code>{run.case_id}</code><span>{run.mutation}</span><b>{run.tool_calls}</b><span>{Math.round(run.duration_ms)} ms</span><em className={run.status}>{run.status}</em></article>)}</div>
    </section>
  );
}
