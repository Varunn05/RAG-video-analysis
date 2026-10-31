import { FormEvent, useState } from "react";

interface Props { onAnalyze: (url: string) => Promise<void>; loading: boolean }
export function AnalysisForm({ onAnalyze, loading }: Props) {
  const [url, setUrl] = useState("");
  async function submit(event: FormEvent) { event.preventDefault(); if (url.trim()) await onAnalyze(url.trim()); }
  return <form className="analysis-form" onSubmit={submit}>
    <label className="url-field"><span className="field-icon" aria-hidden="true">↗</span><input aria-label="YouTube URL" value={url} onChange={event => setUrl(event.target.value)} placeholder="Paste a YouTube video URL" disabled={loading} /></label>
    <button className="primary-button" disabled={loading || !url.trim()}>{loading ? "Analyzing..." : "Analyze video"}<span aria-hidden="true">→</span></button>
  </form>;
}
