from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .schemas import AnalysisReport, AnalysisRequest, Summary
from .workflow import analysis_graph

app = FastAPI(title="YouTube Fact Checker API", version="2.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/analyses", response_model=AnalysisReport)
def analyze_video(request: AnalysisRequest) -> AnalysisReport:
    try:
        state = analysis_graph.invoke({"youtube_url": request.youtube_url})
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Analysis failed: {exc}") from exc

    claims = state.get("results", [])
    statuses = [claim["status"] for claim in claims]
    return AnalysisReport(
        video_id=state["video_id"],
        claims=claims,
        summary=Summary(
            total_claims=len(claims), true=statuses.count("TRUE"), false=statuses.count("FALSE"),
            misleading=statuses.count("MISLEADING"), unverifiable=statuses.count("UNVERIFIABLE"), errors=statuses.count("ERROR"),
        ),
    )
