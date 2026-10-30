import { FormEvent, useState } from "react";

interface Props { onAnalyze: (url: string) => Promise<void>; loading: boolean }
export function AnalysisForm({ onAnalyze, loading }: Props) {
  const [url, setUrl] = useState("");
  async function submit(event: FormEvent) { event.preventDefault(); if (url.trim()) await onAnalyze(url.trim()); }
  return <form className="analysis-form" onSubmit={submit}>
    <input aria-label="YouTube URL" value={url} onChange={event => setUrl(event.target.value)} placeholder="Paste a YouTube video URL" disabled={loading} />
    <button disabled={loading || !url.trim()}>{loading ? "Analyzing…" : "Analyze video"}</button>
  </form>;
}
