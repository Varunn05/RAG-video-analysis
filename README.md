# YouTube Fact Checker

An evidence-first fact-checking application for YouTube videos. The frontend is a React single-page application and the backend is a FastAPI service whose analysis pipeline is expressed as a LangGraph workflow.

## Architecture

```text
React + Vite  →  FastAPI  →  LangGraph
                              ├─ identify video
                              ├─ fetch YouTube transcript
                              ├─ extract claims (Groq / LangChain)
                              └─ research (Tavily) + judge (Groq / LangChain)
```

The graph fits the multi-stage, stateful workflow; LangChain supplies the model client and message abstractions. Provider integrations are isolated in `backend/app/services`, so graph checkpoints, retries, or a human-review branch can be added later.

## Project layout

- `backend/app/main.py` — HTTP API and validation boundary.
- `backend/app/workflow.py` — LangGraph nodes and pipeline definition.
- `backend/app/services/` — YouTube, search, and LLM integrations.
- `frontend/src/components/` — small reusable React UI components.
- `frontend/src/api.ts`, `types.ts`, `utils.ts` — transport, domain types, and pure UI helpers.
- `ui.py`, `main.py`, `fact_checker.py` — legacy Streamlit/CLI implementation, retained during migration.

## Setup

Create a `.env` file in the repository root:

```env
GROQ_API_KEY=gsk_...
TAVILY_API_KEY=tvly-...
# Optional override (this is also the default)
GROQ_MODEL=openai/gpt-oss-120b
CORS_ORIGINS=["http://localhost:5173"]
```

Install and run the backend:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn backend.app.main:app --reload --port 8000
```

In another terminal, run the React client:

```bash
cd frontend
npm install
npm run dev
```

Open the Vite address (normally `http://localhost:5173`). Vite proxies `/api` to the FastAPI server in development.

## API

`POST /api/analyses`

```json
{ "youtube_url": "https://www.youtube.com/watch?v=VIDEO_ID" }
```

The response includes `video_id`, a verdict-count `summary`, and fact-checked `claims` with sources. `GET /api/health` is available for service checks.

## Notes

This first API implementation is synchronous: a request completes when the report is ready. For videos with many claims, the natural next evolution is a persisted LangGraph run plus a status/SSE endpoint.
