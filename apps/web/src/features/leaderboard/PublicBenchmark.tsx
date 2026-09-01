import type { PublicLeaderboardEntry } from "../../shared/types";

export function PublicBenchmark({ entries }: { entries: PublicLeaderboardEntry[] }) {
  return (
    <section className="workspace-page benchmark-page">
      <header className="page-heading"><div><span className="section-index">PUBLIC BENCHMARK</span><h1>公开可靠性基准</h1><p>只比较相同 Standard 测试包和 Runner 版本。自报告结果不会进入正式名次。</p></div><a className="text-action" href="https://github.com/lemon-neko/agent-reliability-arena" target="_blank" rel="noreferrer">通过 GitHub PR 提交 ↗</a></header>
      {entries.some((entry) => entry.demo) && <div className="demo-note"><b>演示排行榜</b><span>以下项目为交互演示数据，不代表真实第三方认证。</span></div>}
      <div className="benchmark-table"><header><span>Rank / Agent</span><span>Score</span><span>Gate</span><span>Verification</span><span>Evaluated</span></header>{entries.map((entry) => <article key={entry.id}><div><b>{String(entry.rank).padStart(2, "0")}</b><span><strong>{entry.agent_name}</strong><small>{entry.agent_version} · {entry.suite_version} · 波动 {entry.volatility_percent}%</small></span></div><div className="benchmark-score"><strong>{entry.score}</strong><i>{entry.grade}</i></div><span className={`benchmark-verdict ${entry.verdict}`}>{entry.verdict === "ready" ? "通过" : entry.verdict === "conditional" ? "有条件" : "未通过"}</span><span className={`verification ${entry.verification}`}>{entry.verification === "verified" ? "官方复测" : "可复现"}</span><time>{new Date(entry.evaluated_at).toLocaleDateString("zh-CN")}</time></article>)}</div>
      {!entries.length && <div className="empty-state large"><b>00</b><h2>等待第一份可复现提交</h2><p>本地报告默认私有；只有作者主动提交的脱敏证明包才会出现在这里。</p></div>}
    </section>
  );
}
