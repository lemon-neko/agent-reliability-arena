import type { AgentTarget, Assessment, PublicLeaderboardEntry, RiskCase } from "../../shared/types";

export function RiskOverview({
  cases,
  targets,
  assessments,
  leaderboard,
  onNavigate,
}: {
  cases: RiskCase[];
  targets: AgentTarget[];
  assessments: Assessment[];
  leaderboard: PublicLeaderboardEntry[];
  onNavigate: (view: "targets" | "audit" | "benchmark") => void;
}) {
  const completed = assessments.filter((item) => item.status === "completed").length;
  return (
    <div className="overview-page">
      <section className="overview-hero">
        <div className="hero-copy">
          <span className="section-index">01 / PRIVATE RISK LAB</span>
          <h1>你的 Agent，<br /><em>真的敢上线吗？</em></h1>
          <p>
            把自研 HTTP Agent 接入受控工具网关，用 12–180 次可复现测试检查注入、
            泄露、越权、审批绕过、幻觉与失控循环。
          </p>
          <div className="hero-actions">
            <button className="primary-action" onClick={() => onNavigate("audit")}>开始一次风险体检</button>
            <button className="text-action" onClick={() => onNavigate("benchmark")}>查看公开基准 ↗</button>
          </div>
        </div>
        <aside className="hero-proof" aria-label="评测方法摘要">
          <div className="proof-orbit"><span>ARA</span><i /></div>
          <dl>
            <div><dt>测试基线</dt><dd>{cases.length || 12}</dd></div>
            <div><dt>标准运行</dt><dd>72×</dd></div>
            <div><dt>核心裁判</dt><dd>确定性</dd></div>
          </dl>
        </aside>
      </section>

      <section className="operating-strip" aria-label="当前工作区">
        <div><span>已接入 Agent</span><strong>{targets.length}</strong><small>Endpoint 配置留在本机</small></div>
        <div><span>已完成报告</span><strong>{completed}</strong><small>JSON · HTML · 可打印 PDF</small></div>
        <div><span>公开认证</span><strong>{leaderboard.length}</strong><small>仅统计可复现与官方复测</small></div>
        <button onClick={() => onNavigate("targets")}><b>+</b><span>注册 Agent Endpoint</span></button>
      </section>

      <section className="method-section">
        <header>
          <span className="section-index">02 / HOW EVIDENCE IS MADE</span>
          <h2>不是问卷，也不是另一个模型的主观评分。</h2>
        </header>
        <ol className="method-flow">
          <li><span>01</span><div><h3>固定攻击面</h3><p>版本化风险用例与稳定 Seed，让每次复测都有相同起点。</p></div></li>
          <li><span>02</span><div><h3>受控执行</h3><p>Agent 只能返回工具意图，文件、SQL 和业务动作都由隔离网关执行。</p></div></li>
          <li><span>03</span><div><h3>证据落盘</h3><p>每个结论都能回到调用顺序、策略阻断和最终状态。</p></div></li>
          <li><span>04</span><div><h3>安全门禁</h3><p>单个 High 或 Critical 风险不会被平均分掩盖。</p></div></li>
        </ol>
      </section>
    </div>
  );
}
