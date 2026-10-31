import type { Summary, Verdict } from "./types";

export const verdictMeta: Record<Verdict, { label: string; icon: string }> = {
  TRUE: { label: "True", icon: "✓" }, FALSE: { label: "False", icon: "×" },
  MISLEADING: { label: "Misleading", icon: "!" }, UNVERIFIABLE: { label: "Unverifiable", icon: "?" }, ERROR: { label: "Error", icon: "!" },
};

export function secondsFromTimestamp(timestamp: string): number {
  const raw = timestamp.trim().replace(/^\[|\]$/g, "").replace(/s$/i, "");
  if (raw.includes(":")) {
    const parts = raw.split(":").map(Number);
    if (parts.length >= 2 && parts.every(Number.isFinite)) return Math.floor(parts.reduce((total, value) => total * 60 + value, 0));
  }
  const match = raw.match(/-?\d+(?:\.\d+)?/);
  return Math.max(0, Math.floor(match ? Number(match[0]) : 0));
}
export function formatTimestamp(timestamp: string): string { const seconds = secondsFromTimestamp(timestamp); return `${String(Math.floor(seconds / 60)).padStart(2, "0")}:${String(seconds % 60).padStart(2, "0")}`; }
export function trustScore(summary: Summary): number { if (!summary.total_claims) return 0; return Math.round(((summary.true + summary.misleading * 0.5) / summary.total_claims) * 100); }
