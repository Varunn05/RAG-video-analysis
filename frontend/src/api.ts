import type { Report } from "./types";

export async function analyzeVideo(youtubeUrl: string): Promise<Report> {
  const response = await fetch("/api/analyses", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ youtube_url: youtubeUrl }),
  });
  const body = await response.json();
  if (!response.ok) throw new Error(body.detail ?? "Unable to analyze this video.");
  return body;
}
