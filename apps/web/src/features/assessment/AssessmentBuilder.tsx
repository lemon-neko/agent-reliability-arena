import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState, type FormEvent } from "react";
import { api } from "../../shared/api";
import type { AgentTarget, AssessmentDetail, AssessmentProfile, RiskCase } from "../../shared/types";

const profiles: Array<{ id: AssessmentProfile; runs: number; note: string }> = [
  { id: "quick", runs: 12, note: "接入冒烟" },
  { id: "standard", runs: 72, note: "发布前基线" },
  { id: "deep", runs: 180, note: "深度回归" },
];

export function AssessmentBuilder({
  targets,
  cases,
  onAssessment,
}: {
  targets: AgentTarget[];
  cases: RiskCase[];
  onAssessment: (detail: AssessmentDetail) => void;
}) {
  const queryClient = useQueryClient();
  const [profile, setProfile] = useState<AssessmentProfile>("standard");
  const [targetId, setTargetId] = useState(targets[0]?.id ?? "");
  useEffect(() => {
    if (!targetId && targets[0]) setTargetId(targets[0].id);
  }, [targetId, targets]);
  const mutation = useMutation({
    mutationFn: api.createAssessment,
    onSuccess: async ({ assessment }) => {
      let detail = await api.assessment(assessment.id);
      onAssessment(detail);
      const streamCompleted = await new Promise<boolean>((resolve) => {
        const source = api.assessmentEvents(assessment.id);
        const refresh = async () => {
          detail = await api.assessment(assessment.id);
          onAssessment(detail);
        };
        source.addEventListener("progress", refresh);
        source.addEventListener("end", async () => {
          await refresh();
          source.close();
          resolve(true);
        });
        source.onerror = () => {
          source.close();
          resolve(false);
        };
      });
      if (streamCompleted) {
        queryClient.invalidateQueries({ queryKey: ["risk-assessments"] });
        return;
      }
      while (["queued", "running"].includes(detail.assessment.status)) {
        await new Promise((resolve) => window.setTimeout(resolve, 700));
        detail = await api.assessment(assessment.id);
        onAssessment(detail);
      }
      queryClient.invalidateQueries({ queryKey: ["risk-assessments"] });
    },
  });
  const submit = (event: FormEvent) => {
    event.preventDefault();
    mutation.mutate({
      target_id: targetId,
      name: `风险体检 · ${new Date().toLocaleDateString("zh-CN")}`,
      profile,
      seed: 20260901,
      concurrency: profile === "quick" ? 2 : 4,
    });
  };
  return (
    <section className="workspace-page">
      <header className="page-heading"><div><span className="section-index">NEW ASSESSMENT</span><h1>发起风险体检</h1><p>真实运行会从后端调用 ara-step/1 Endpoint，并把所有工具动作留在沙箱内。</p></div></header>
      <form className="assessment-form" onSubmit={submit}>
        <fieldset><legend><span>01</span> 选择 Agent</legend><select value={targetId} required onChange={(event) => setTargetId(event.target.value)}><option value="" disabled>请选择本地项目</option>{targets.map((target) => <option key={target.id} value={target.id}>{target.name} · {target.version}</option>)}</select><p>{targets.length ? "凭证由后端从环境变量读取。" : "请先在 Agent 项目中注册 Endpoint。"}</p></fieldset>
        <fieldset><legend><span>02</span> 测试档位</legend><div className="profile-options">{profiles.map((item) => <label key={item.id} className={profile === item.id ? "selected" : ""}><input type="radio" checked={profile === item.id} onChange={() => setProfile(item.id)} /><b>{item.id}</b><strong>{item.runs}</strong><small>{item.note}</small></label>)}</div></fieldset>
        <fieldset><legend><span>03</span> 覆盖面</legend><div className="coverage-list">{cases.slice(0, 8).map((item) => <span key={item.id}>{item.title}</span>)}</div></fieldset>
        {mutation.isError && <p className="form-error">{mutation.error.message}</p>}
        <button className="audit-launch" disabled={!targetId || mutation.isPending}><span>{mutation.isPending ? "正在执行…" : `执行 ${profiles.find((item) => item.id === profile)?.runs} 项测试`}</span><small>Seed 20260901 · 最多 4 workers</small></button>
      </form>
    </section>
  );
}
