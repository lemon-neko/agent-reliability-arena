import type { Agent } from "./types";

const familyLabels: Record<string, string> = { file: "文件操作", sql: "SQL", rag: "RAG", approval: "人工审批", security: "安全攻防" };
const statusLabels: Record<string, string> = { queued: "排队中", running: "运行中", waiting_approval: "等待审批", completed: "已完成", failed: "失败", cancelled: "已取消" };

export const familyLabel = (family: string) => familyLabels[family] ?? family;
export const statusLabel = (status: string) => statusLabels[status] ?? status;

export function agentLabel(agent: Agent) {
  const model = agent.model === "fake-deterministic" ? "确定性假模型" : agent.model;
  if (agent.runtime === "minimal") return `最小工具 Agent · ${model}`;
  if (agent.runtime === "langgraph") return `LangGraph Agent · ${model}`;
  return agent.name;
}
