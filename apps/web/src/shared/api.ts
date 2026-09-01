import type { Agent, FrozenReport, LeaderboardRow, Run, Scenario, TraceEvent } from "./types";

export const DEMO_MODE = import.meta.env.VITE_DEMO_MODE === "true";
let frozen: Promise<FrozenReport> | undefined;

function frozenReport() {
  frozen ??= fetch(`${import.meta.env.BASE_URL}data/report.json`).then((response) => {
    if (!response.ok) throw new Error("冻结战报暂时不可用");
    return response.json() as Promise<FrozenReport>;
  });
  return frozen;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, init);
  if (!response.ok) throw new Error((await response.text()) || `请求失败：${response.status}`);
  return response.json() as Promise<T>;
}

export const api = {
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
