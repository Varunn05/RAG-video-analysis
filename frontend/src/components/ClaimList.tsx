import type { Claim, Verdict } from "../types";
import { formatTimestamp, secondsFromTimestamp, verdictMeta } from "../utils";

interface Props { claims: Claim[]; activeFilter: Verdict | "ALL"; onFilter: (filter: Verdict | "ALL") => void; onJump: (seconds: number) => void }
const filters: Array<Verdict | "ALL"> = ["ALL", "TRUE", "FALSE", "MISLEADING", "UNVERIFIABLE"];
export function ClaimList({ claims, activeFilter, onFilter, onJump }: Props) {
  const visible = activeFilter === "ALL" ? claims : claims.filter(claim => claim.status === activeFilter);
  return <section className="panel claims"><h2>Fact-checked claims</h2><div className="filters">{filters.map(filter => <button key={filter} className={filter === activeFilter ? "active" : ""} onClick={() => onFilter(filter)}>{filter === "ALL" ? "All" : verdictMeta[filter].label}</button>)}</div>
    {visible.map((claim, index) => <article className={`claim ${claim.status.toLowerCase()}`} key={`${claim.timestamp}-${index}`}><div className="claim-header"><span>{formatTimestamp(claim.timestamp)}</span><strong>{verdictMeta[claim.status].icon} {verdictMeta[claim.status].label} · {claim.confidence}</strong><button onClick={() => onJump(secondsFromTimestamp(claim.timestamp))}>Jump</button></div><h3>{claim.claim}</h3><p>{claim.explanation}</p>{claim.sources.length > 0 && <details><summary>Evidence and sources</summary>{claim.sources.map((source, sourceIndex) => <div className="source" key={source.url || sourceIndex}><a href={source.url} target="_blank" rel="noreferrer">{source.title}</a><p>{source.snippet}</p></div>)}</details>}</article>)}
    {!visible.length && <p className="empty">No claims match this filter.</p>}
  </section>;
}
