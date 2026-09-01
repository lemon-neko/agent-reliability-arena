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

export type RiskCase = {
  id: string;
  version: string;
  title: string;
  description: string;
  category: string;
  dimension: string;
  severity: "critical" | "high" | "medium" | "low" | "info";
  tags: string[];
  max_steps: number;
  timeout_seconds: number;
};

export type AgentTarget = {
  id: string;
  name: string;
  description: string;
  endpoint_url: string;
  protocol_version: "ara-step/1";
  network_scope: "local" | "public";
  auth_header_name?: string | null;
  auth_env_var?: string | null;
  repository_url?: string | null;
  version: string;
  capabilities: string[];
  created_at: string;
  updated_at: string;
};

export type AssessmentProfile = "quick" | "standard" | "deep";

export type Assessment = {
  id: string;
  target_id: string;
  name: string;
  profile: AssessmentProfile;
  suite_version: string;
  seed: number;
  repetitions: number;
  concurrency: number;
  status: "queued" | "running" | "completed" | "failed" | "cancelled";
  total_runs: number;
  completed_runs: number;
  failed_runs: number;
  cancel_requested: boolean;
  created_at: string;
  started_at?: string | null;
  completed_at?: string | null;
};

export type RiskTestRun = {
  id: string;
  assessment_id: string;
  target_id: string;
  case_id: string;
  case_version: string;
  variant_id: string;
  mutation: string;
  seed: number;
  repetition: number;
  status: string;
  answer: string;
  error: string;
  tool_calls: number;
  duration_ms: number;
};

export type Finding = {
  id: string;
  assessment_id: string;
  test_run_id: string;
  case_id: string;
  category: string;
  dimension: string;
  severity: "critical" | "high" | "medium" | "low" | "info";
  confidence: "deterministic";
  title: string;
  summary: string;
  expected: string;
  observed: string;
  evidence_event_ids: string[];
  reproduction: string;
  remediation: string;
  occurrences: number;
};

export type RiskDimensionScores = {
  security_privacy: number;
  authorization_control: number;
  side_effect_safety: number;
  correctness_grounding: number;
  resilience_idempotency: number;
  efficiency_resources: number;
};

export type RiskReport = {
  schema_version: 1;
  assessment_id: string;
  target_id: string;
  target_name: string;
  target_version: string;
  repository_url?: string | null;
  suite_version: string;
  profile: AssessmentProfile;
  generated_at: string;
  raw_score: number;
  final_score: number;
  grade: "A" | "B" | "C" | "D" | "E";
  verdict: "ready" | "conditional" | "not_recommended";
  gate_reasons: string[];
  dimension_scores: RiskDimensionScores;
  coverage: Record<string, number | string>;
  finding_counts: Record<string, number>;
  findings: Finding[];
  limitations: string[];
};

export type AssessmentDetail = {
  assessment: Assessment;
  runs: RiskTestRun[];
  findings: Finding[];
  report: RiskReport | null;
};

export type PublicLeaderboardEntry = {
  rank: number;
  id: string;
  agent_name: string;
  agent_version: string;
  repository_url: string;
  suite_version: string;
  profile: "standard";
  score: number;
  grade: string;
  verdict: string;
  finding_counts: Record<string, number>;
  volatility_percent: number;
  report_sha256: string;
  runner_version: string;
  verification: "self_reported" | "reproducible" | "verified";
  evaluated_at: string;
  submitted_at: string;
  demo?: boolean;
};

export type FrozenRiskDemo = {
  schema_version: 1;
  frozen_at: string;
  cases: RiskCase[];
  targets: AgentTarget[];
  reports: Record<string, RiskReport>;
  leaderboard: PublicLeaderboardEntry[];
};
