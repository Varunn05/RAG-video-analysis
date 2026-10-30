export type Verdict = "TRUE" | "FALSE" | "MISLEADING" | "UNVERIFIABLE" | "ERROR";

export interface Source { title: string; url: string; snippet: string }
export interface Claim { timestamp: string; claim: string; status: Verdict; explanation: string; confidence: string; source_url: string | null; sources: Source[] }
export interface Summary { total_claims: number; true: number; false: number; misleading: number; unverifiable: number; errors: number }
export interface Report { video_id: string; summary: Summary; claims: Claim[] }
