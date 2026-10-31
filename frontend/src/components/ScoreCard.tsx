import type { CSSProperties } from "react";
import type { Summary, Verdict } from "../types";
import { trustScore } from "../utils";

interface Props {
  summary: Summary;
  activeFilter: Verdict | "ALL";
  onFilter: (filter: Verdict | "ALL") => void;
}

const stats: Array<{ verdict: Verdict; count: keyof Pick<Summary, "true" | "false" | "misleading" | "unverifiable">; label: string; className: string }> = [
  { verdict: "TRUE", count: "true", label: "True", className: "true" },
  { verdict: "FALSE", count: "false", label: "False", className: "false" },
  { verdict: "MISLEADING", count: "misleading", label: "Misleading", className: "misleading" },
  { verdict: "UNVERIFIABLE", count: "unverifiable", label: "Unverified", className: "unverifiable" },
];

export function ScoreCard({ summary, activeFilter, onFilter }: Props) {
  const score = trustScore(summary);
  const label = score >= 80 ? "Highly trustworthy" : score >= 60 ? "Mostly accurate" : score >= 40 ? "Mixed accuracy" : "Low accuracy";
  return <section className="panel score"><div className="panel-label">Reliability score</div><div className="score-top"><div><div className="score-value">{score}<small>%</small></div><p>{label}</p></div><div className="score-ring" style={{ "--score": `${score * 3.6}deg` } as CSSProperties}><span>{score}</span></div></div><div className="score-bar"><span style={{ width: `${score}%` }} /></div><div className="stats">{stats.map(({ verdict, count, label: statLabel, className }) => {
    const selected = activeFilter === verdict;
    return <button key={verdict} className={`stat ${className}${selected ? " active" : ""}`} onClick={() => onFilter(selected ? "ALL" : verdict)} aria-pressed={selected} title={selected ? "Show all claims" : `Show ${statLabel.toLowerCase()} claims`}><b>{summary[count]}</b> {statLabel}</button>;
  })}</div></section>;
}
