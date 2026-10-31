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
  async function handleAnalyze(url: string) {
    setLoading(true); setError(null);
    try { setReport(await analyzeVideo(url)); setFilter("ALL"); setStartAt(0); }
    catch (err) { setError(err instanceof Error ? err.message : "Unable to analyze this video."); }
    finally { setLoading(false); }
  }
  return <main>
    {!report && <header className="hero" id="top"><div className="hero-copy-wrap"><p className="eyebrow">AI-powered fact checking</p><h1>Know what's true<br />before you <em>share.</em></h1><p className="hero-copy">Turn any YouTube video into a clear, source-backed fact check. One link is all it takes.</p></div><div className="hero-art" aria-hidden="true"><span className="orbit orbit-one" /><span className="orbit orbit-two" /><span className="art-card"><b>96</b><small>Trust score</small></span><span className="art-caption">ANALYZE<br />WITH CLARITY</span></div></header>}
    <section className="analyzer"><div className="analyzer-heading"><div><p className="eyebrow">Start an analysis</p><h2>Check a video</h2></div><span>YouTube supported</span></div><AnalysisForm onAnalyze={handleAnalyze} loading={loading} /></section>
    {error && <p className="error" role="alert">{error}</p>}
    {!report && !loading && <section className="welcome"><div className="welcome-heading"><div><p className="eyebrow">What happens next</p><h2>Clarity in three steps.</h2></div><p>Built for the moments when you need more than a hunch.</p></div><div className="welcome-grid"><article><span>01</span><h3>Read the video</h3><p>We locate the factual claims worth checking.</p></article><article><span>02</span><h3>Verify evidence</h3><p>Each claim is checked against reliable sources.</p></article><article><span>03</span><h3>See the full picture</h3><p>Review verdicts in a simple, timestamped report.</p></article></div></section>}
    {loading && <section className="loading-state" aria-live="polite"><span className="loading-orbit" /><div><p className="eyebrow">Analysis in progress</p><h2>Reading the video and checking its claims...</h2><p>This can take a moment for longer videos.</p></div></section>}
    {report && <><section className="report-heading"><div><p className="eyebrow">Analysis complete</p><h2>Evidence report</h2></div><p>{report.summary.total_claims} claims found in this video</p></section><div className="dashboard"><aside><VideoPanel videoId={report.video_id} startAt={startAt} /><ScoreCard summary={report.summary} activeFilter={filter} onFilter={setFilter} /></aside><ClaimList claims={report.claims} activeFilter={filter} onFilter={setFilter} onJump={setStartAt} /></div></>}
  </main>;
}
