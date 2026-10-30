import { useState } from "react";
import { analyzeVideo } from "./api";
import { AnalysisForm } from "./components/AnalysisForm";
import { ClaimList } from "./components/ClaimList";
import { ScoreCard } from "./components/ScoreCard";
import { VideoPanel } from "./components/VideoPanel";
import type { Report, Verdict } from "./types";

export default function App() {
  const [report, setReport] = useState<Report | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<Verdict | "ALL">("ALL");
  const [startAt, setStartAt] = useState(0);
  async function handleAnalyze(url: string) { setLoading(true); setError(null); try { setReport(await analyzeVideo(url)); setFilter("ALL"); setStartAt(0); } catch (err) { setError(err instanceof Error ? err.message : "Unable to analyze this video."); } finally { setLoading(false); } }
  return <main><header><p className="eyebrow">Evidence-first AI</p><h1>YouTube Fact Checker</h1><p>Check factual claims in a video against web research.</p></header><AnalysisForm onAnalyze={handleAnalyze} loading={loading} />{error && <p className="error" role="alert">{error}</p>}{report && <div className="dashboard"><aside><VideoPanel videoId={report.video_id} startAt={startAt} /><ScoreCard summary={report.summary} /></aside><ClaimList claims={report.claims} activeFilter={filter} onFilter={setFilter} onJump={setStartAt} /></div>}</main>;
}
