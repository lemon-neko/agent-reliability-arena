import type {
  Agent,
  AgentTarget,
  Assessment,
  AssessmentDetail,
  AssessmentProfile,
  FrozenReport,
  FrozenRiskDemo,
  LeaderboardRow,
  PublicLeaderboardEntry,
  RiskCase,
  RiskReport,
  Run,
  Scenario,
  TraceEvent,
} from "./types";

export const DEMO_MODE = import.meta.env.VITE_DEMO_MODE === "true";
let frozen: Promise<FrozenReport> | undefined;
let frozenRisk: Promise<FrozenRiskDemo> | undefined;

function frozenReport() {
  frozen ??= fetch(`${import.meta.env.BASE_URL}data/report.json`).then((response) => {
    if (!response.ok) throw new Error("冻结战报暂时不可用");
    return response.json() as Promise<FrozenReport>;
  });
  return frozen;
}

function frozenRiskDemo() {
  frozenRisk ??= fetch(`${import.meta.env.BASE_URL}data/risk-demo.json`).then((response) => {
    if (!response.ok) throw new Error("风险演示数据暂时不可用");
    return response.json() as Promise<FrozenRiskDemo>;
  });
  return frozenRisk;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, init);
  if (!response.ok) throw new Error((await response.text()) || `请求失败：${response.status}`);
  return response.json() as Promise<T>;
}

export const api = {
  riskCases: async (): Promise<RiskCase[]> =>
    DEMO_MODE ? (await frozenRiskDemo()).cases : request("/api/v1/risk-cases"),
  agentTargets: async (): Promise<AgentTarget[]> =>
    DEMO_MODE ? (await frozenRiskDemo()).targets : request("/api/v1/agent-targets"),
  assessments: async (): Promise<Assessment[]> =>
    DEMO_MODE ? [] : request("/api/v1/assessments"),
  publicLeaderboard: async (): Promise<PublicLeaderboardEntry[]> =>
    DEMO_MODE
      ? (await frozenRiskDemo()).leaderboard
      : request("/api/v1/public-leaderboard"),
  demoReport: async (targetId: string): Promise<RiskReport> => {
    const report = (await frozenRiskDemo()).reports[targetId];
    if (!report) throw new Error("没有找到该演示 Agent 的冻结报告");
    return report;
  },
  createAgentTarget: (input: {
    name: string;
    description: string;
    endpoint_url: string;
    network_scope: "local" | "public";
    auth_header_name?: string;
    auth_env_var?: string;
    repository_url?: string;
    version: string;
    capabilities: string[];
  }) => {
    if (DEMO_MODE) throw new Error("公开演示不会保存 Agent 配置");
    return request<AgentTarget>("/api/v1/agent-targets", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(input),
    });
  },
  validateAgentTarget: (id: string) => {
    if (DEMO_MODE) throw new Error("公开演示不会连接 Agent Endpoint");
    return request<{ valid: boolean; protocol: string; response: string }>(
      `/api/v1/agent-targets/${id}/validate`,
      { method: "POST" },
    );
  },
  createAssessment: (input: {
    target_id: string;
    name: string;
    profile: AssessmentProfile;
    seed: number;
    concurrency?: number;
  }) => {
    if (DEMO_MODE) throw new Error("公开演示不会发起真实评测");
    return request<{ assessment: Assessment; run_count: number }>("/api/v1/assessments", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(input),
    });
  },
  assessment: (id: string) => request<AssessmentDetail>(`/api/v1/assessments/${id}`),
  assessmentEvents: (id: string) => {
    if (DEMO_MODE) throw new Error("公开演示没有后台 SSE 任务");
    return new EventSource(`/api/v1/assessments/${id}/events`);
  },
  riskReport: (id: string) => request<RiskReport>(`/api/v1/reports/${id}`),
  cancelAssessment: (id: string) => {
    if (DEMO_MODE) throw new Error("公开演示没有后台任务");
    return request<Assessment>(`/api/v1/assessments/${id}/cancel`, { method: "POST" });
  },
  createAttestation: (id: string) => {
    if (DEMO_MODE) throw new Error("公开演示不会生成可提交的证明包");
    return request(`/api/v1/reports/${id}/attestation`, { method: "POST" });
  },
  scenarios: async (): Promise<Scenario[]> =>
    DEMO_MODE ? (await frozenReport()).scenarios : request("/api/scenarios"),
  agents: async (): Promise<Agent[]> =>
    DEMO_MODE ? (await frozenReport()).agents : request("/api/agents"),
  leaderboard: async (): Promise<LeaderboardRow[]> =>
    DEMO_MODE ? (await frozenReport()).leaderboard : request("/api/leaderboard"),
  sampleRuns: async () => (DEMO_MODE ? (await frozenReport()).sample_runs : []),
  createTournament: async (input: {
    name: string;
    agent_ids: string[];
    scenario_ids: string[];
    repetitions: number;
  }) => {
    if (DEMO_MODE) throw new Error("公开演示为只读模式");
    return request<{ tournament: { id: string }; run_count: number }>("/api/tournaments", {
      method: "POST",
      headers: { "Content-Type": "application/json", "Idempotency-Key": crypto.randomUUID() },
      body: JSON.stringify(input),
    });
  },
  tournament: (id: string) => request<{ tournament: unknown; runs: Run[] }>(`/api/tournaments/${id}`),
  run: (id: string) => request<{ run: Run; evaluation: unknown; events: TraceEvent[] }>(`/api/runs/${id}`),
  decideApproval: (runId: string, approvalId: string, decision: "approve" | "reject") =>
    request(`/api/runs/${runId}/approvals/${approvalId}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ decision }),
    }),
};
