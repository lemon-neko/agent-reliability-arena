import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { LeaderboardRow } from "../../shared/types";

export function Leaderboard({ rows }: { rows: LeaderboardRow[] }) {
  return <div className="leader-grid"><section className="panel"><div className="section-head"><div><span className="eyebrow">确定性核心评分</span><h2>谁更稳定，分数说话</h2></div></div><table><thead><tr><th>排名</th><th>Agent</th><th>平均分</th><th>运行次数</th><th>得分区间</th></tr></thead><tbody>{rows.map((row, index) => <tr key={row.agent_id}><td>{index + 1}</td><td>{row.agent_id}</td><td><strong>{row.mean_score}</strong></td><td>{row.runs}</td><td>{row.min_score}–{row.max_score}</td></tr>)}</tbody></table></section><section className="panel chart-panel"><ResponsiveContainer width="100%" height={340}><BarChart data={rows}><CartesianGrid strokeDasharray="3 3" stroke="#233049" /><XAxis dataKey="agent_id" stroke="#8190a9" /><YAxis domain={[0, 100]} stroke="#8190a9" /><Tooltip /><Bar dataKey="mean_score" name="平均分" fill="#58e0b7" radius={[6, 6, 0, 0]} /></BarChart></ResponsiveContainer></section></div>;
}
