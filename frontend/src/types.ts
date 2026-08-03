export type Scenario = {
  id: string;
  version: string;
  title: string;
  description: string;
  family: string;
  tags: string[];
  max_steps: number;
};

export type Agent = {
  id: string;
  name: string;
  runtime: "minimal" | "langgraph";
  model: string;
  base_url: string;
};

export type Score = {
  correctness: number;
  safety: number;
  resilience: number;
  efficiency: number;
};

export type Evaluation = {
  run_id: string;
  score: Score;
  passed: boolean;
  latency_ms: number;
  input_tokens: number;
  output_tokens: number;
  estimated_cost_usd: number;
};

export type Run = {
  id: string;
  tournament_id: string;
  scenario_id: string;
  agent_id: string;
  repetition: number;
  status: string;
  answer: string;
  error: string;
};

export type TraceEvent = {
  id: string;
  sequence: number;
  kind: string;
  name: string;
  payload: Record<string, unknown>;
  duration_ms?: number;
};

export type LeaderboardRow = {
  agent_id: string;
  mean_score: number;
  runs: number;
  min_score: number;
  max_score: number;
};

export type FrozenReport = {
  schema_version: number;
  frozen_at: string;
  scenarios: Scenario[];
  agents: Agent[];
  leaderboard: LeaderboardRow[];
  sample_runs: Array<{ run: Run; evaluation: Evaluation; events: TraceEvent[] }>;
};
