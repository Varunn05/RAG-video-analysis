from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from .services.llm import extract_claims, judge_claim
from .services.research import research_claim
from .services.youtube import extract_video_id, fetch_transcript


class AnalysisState(TypedDict, total=False):
    youtube_url: str
    video_id: str
    transcript: str
    claims: list[dict[str, str]]
    results: list[dict]


def identify_video(state: AnalysisState) -> AnalysisState:
    return {"video_id": extract_video_id(state["youtube_url"])}


def load_transcript(state: AnalysisState) -> AnalysisState:
    return {"transcript": fetch_transcript(state["video_id"])}


def find_claims(state: AnalysisState) -> AnalysisState:
    return {"claims": extract_claims(state["transcript"])}


def fact_check_claims(state: AnalysisState) -> AnalysisState:
    results: list[dict] = []
    for claim in state["claims"]:
        try:
            sources = research_claim(claim["claim"])
            evidence = "\n\n".join(f"{s['title']}: {s['snippet']}" for s in sources)
            judgment = judge_claim(claim["claim"], evidence) if sources else {
                "verdict": "UNVERIFIABLE", "confidence": "LOW", "explanation": "No relevant web evidence was found."
            }
            results.append({
                "timestamp": claim["time"], "claim": claim["claim"], "status": judgment["verdict"],
                "confidence": judgment["confidence"], "explanation": judgment["explanation"],
                "source_url": sources[0]["url"] if sources else None, "sources": sources,
            })
        except Exception as exc:
            results.append({"timestamp": claim["time"], "claim": claim["claim"], "status": "ERROR", "confidence": "N/A", "explanation": str(exc), "source_url": None, "sources": []})
    return {"results": results}


def build_workflow():
    graph = StateGraph(AnalysisState)
    graph.add_node("identify_video", identify_video)
    graph.add_node("load_transcript", load_transcript)
    graph.add_node("find_claims", find_claims)
    graph.add_node("fact_check_claims", fact_check_claims)
    graph.add_edge(START, "identify_video")
    graph.add_edge("identify_video", "load_transcript")
    graph.add_edge("load_transcript", "find_claims")
    graph.add_edge("find_claims", "fact_check_claims")
    graph.add_edge("fact_check_claims", END)
    return graph.compile()


analysis_graph = build_workflow()
