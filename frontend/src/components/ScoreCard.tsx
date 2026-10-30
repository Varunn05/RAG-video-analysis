import type { Summary } from "../types";
import { trustScore } from "../utils";

export function ScoreCard({ summary }: { summary: Summary }) {
  const score = trustScore(summary);
  return <section className="panel score"><h2>Truthometer</h2><div className="score-value">{score}<small>%</small></div><progress value={score} max="100" />
    <p>{score >= 80 ? "Highly trustworthy" : score >= 60 ? "Mostly accurate" : score >= 40 ? "Mixed accuracy" : "Low accuracy"}</p>
    <div className="stats"><span>✓ {summary.true} true</span><span>× {summary.false} false</span><span>! {summary.misleading} misleading</span><span>? {summary.unverifiable} unverifiable</span></div>
  </section>;
}
