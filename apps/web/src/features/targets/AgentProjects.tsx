import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";
import { api, DEMO_MODE } from "../../shared/api";
import type { AgentTarget } from "../../shared/types";

export function AgentProjects({ targets }: { targets: AgentTarget[] }) {
  const queryClient = useQueryClient();
  const [showForm, setShowForm] = useState(!targets.length && !DEMO_MODE);
  const [validation, setValidation] = useState<Record<string, string>>({});
  const mutation = useMutation({
    mutationFn: api.createAgentTarget,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["risk-targets"] });
      setShowForm(false);
    },
  });
  const validationMutation = useMutation({
    mutationFn: api.validateAgentTarget,
    onSuccess: (result, targetId) => {
      setValidation((current) => ({
        ...current,
        [targetId]: result.valid ? `协议通过 · ${result.protocol}` : "协议未通过",
      }));
    },
    onError: (error, targetId) => {
      setValidation((current) => ({ ...current, [targetId]: error.message }));
    },
  });

  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    mutation.mutate({
      name: String(data.get("name") || ""),
      description: String(data.get("description") || ""),
      endpoint_url: String(data.get("endpoint_url") || ""),
      network_scope: String(data.get("network_scope")) as "local" | "public",
      version: String(data.get("version") || "unversioned"),
      repository_url: String(data.get("repository_url") || "") || undefined,
      auth_header_name: String(data.get("auth_header_name") || "") || undefined,
      auth_env_var: String(data.get("auth_env_var") || "") || undefined,
      capabilities: ["file", "sql", "rag", "approval"],
    });
  };

  return (
    <section className="workspace-page">
      <header className="page-heading">
        <div><span className="section-index">AGENT PROJECTS</span><h1>被测 Agent</h1><p>这里只保存 Endpoint 元数据和环境变量名称，不保存凭证值。</p></div>
        {!DEMO_MODE && <button className="primary-action" onClick={() => setShowForm((value) => !value)}>{showForm ? "收起表单" : "+ 注册 Agent"}</button>}
      </header>

      {showForm && (
        <form className="target-form" onSubmit={submit}>
          <div className="form-intro"><span>ARA-STEP / 1</span><h2>连接你的自研 Agent</h2><p>平台逐步发送消息和工具定义，Endpoint 每次返回一个工具动作或最终答案。</p></div>
          <label>项目名称<input name="name" required placeholder="例如：订单助手" /></label>
          <label>版本<input name="version" required defaultValue="0.1.0" /></label>
          <label className="wide">Step Endpoint<input name="endpoint_url" type="url" required defaultValue="http://127.0.0.1:8000/examples/agents/hardened/step" /></label>
          <label>网络范围<select name="network_scope" defaultValue="local"><option value="local">本机 loopback</option><option value="public">公网 HTTPS</option></select></label>
          <label>代码仓库<input name="repository_url" type="url" placeholder="公开证明包需要" /></label>
          <label>认证 Header<input name="auth_header_name" placeholder="例如 Authorization" /></label>
          <label>凭证环境变量<input name="auth_env_var" placeholder="例如 MY_AGENT_TOKEN" /></label>
          <label className="wide">说明<textarea name="description" rows={3} placeholder="Agent 的用途和主要工具能力" /></label>
          {mutation.isError && <p className="form-error">{mutation.error.message}</p>}
          <button className="primary-action" disabled={mutation.isPending}>{mutation.isPending ? "正在保存…" : "保存本地配置"}</button>
        </form>
      )}

      <div className="target-ledger">
        {targets.map((target, index) => (
          <article key={target.id}>
            <span className="ledger-number">{String(index + 1).padStart(2, "0")}</span>
            <div className="target-identity"><small>{target.protocol_version}</small><h2>{target.name}</h2><p>{target.description || "尚未添加项目说明。"}</p></div>
            <dl><div><dt>版本</dt><dd>{target.version}</dd></div><div><dt>范围</dt><dd>{target.network_scope}</dd></div><div><dt>凭证</dt><dd>{target.auth_env_var ? "环境变量引用" : "无需认证"}</dd></div></dl>
            <div className="target-endpoint"><code>{DEMO_MODE ? "演示 Endpoint · 不会连接" : target.endpoint_url}</code>{!DEMO_MODE && <button onClick={() => validationMutation.mutate(target.id)} disabled={validationMutation.isPending && validationMutation.variables === target.id}>{validationMutation.isPending && validationMutation.variables === target.id ? "正在验证…" : "验证 ara-step/1"}</button>}{validation[target.id] && <small>{validation[target.id]}</small>}</div>
          </article>
        ))}
        {!targets.length && <div className="empty-state"><b>∅</b><h2>还没有 Agent 项目</h2><p>先注册一个 ara-step/1 Endpoint，再发起风险体检。</p></div>}
      </div>
    </section>
  );
}
