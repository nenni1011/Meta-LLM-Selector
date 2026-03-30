"""FastAPI web server for Meta-LLM-Selector with SSE streaming."""

from __future__ import annotations

import json
import os
import sys
import threading
from queue import Queue, Empty

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

# Load .env from project root
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

# Suppress CrewAI interactive prompts
os.environ.setdefault("CREWAI_TRACING_ENABLED", "false")

app = FastAPI(title="Meta-LLM-Selector", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class AnalyzeRequest(BaseModel):
    prompt: str


def _run_pipeline_thread(prompt: str, queue: Queue):
    """Run the pipeline in a background thread, emitting events to the queue."""

    def on_progress(event: dict):
        queue.put(event)

    try:
        from crew import run_pipeline
        from state import MetaLLMState

        state = run_pipeline(prompt, on_progress=on_progress)

        # Serialize result
        recs = []
        for r in state.recommendations:
            recs.append({
                "tier": r.tier,
                "model_name": r.model_name,
                "provider": r.provider,
                "input_cost_per_million": r.input_cost_per_million,
                "output_cost_per_million": r.output_cost_per_million,
                "context_window": r.context_window,
                "speed_label": r.speed_label,
                "justification": r.justification,
            })

        scored = []
        for s in sorted(state.scored_candidates, key=lambda x: x.overall_score, reverse=True):
            scored.append({
                "name": s.name,
                "provider": s.provider,
                "tier": s.tier,
                "overall_score": s.overall_score,
                "cost_score": s.cost_score,
                "performance_score": s.performance_score,
                "speed_score": s.speed_score,
                "fit_score": s.fit_score,
            })

        queue.put({
            "type": "result",
            "data": {
                "task_type": state.task_type,
                "use_case_detail": state.use_case_detail,
                "budget_tier": state.budget_tier,
                "recommendations": recs,
                "scored_candidates": scored,
            },
        })
    except Exception as e:
        queue.put({"type": "error", "message": str(e)})
    finally:
        queue.put({"type": "done"})


@app.post("/api/analyze")
async def analyze(request: AnalyzeRequest):
    """Start analysis and stream progress via SSE."""
    import asyncio

    queue: Queue = Queue()
    thread = threading.Thread(
        target=_run_pipeline_thread,
        args=(request.prompt, queue),
        daemon=True,
    )
    thread.start()

    async def event_stream():
        while True:
            try:
                event = queue.get(timeout=0.3)
                yield f"data: {json.dumps(event)}\n\n"
                if event.get("type") in ("done", "error"):
                    break
            except Empty:
                if not thread.is_alive():
                    # Drain remaining
                    while not queue.empty():
                        event = queue.get_nowait()
                        yield f"data: {json.dumps(event)}\n\n"
                    break
                yield ": heartbeat\n\n"
            await asyncio.sleep(0.1)

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.get("/api/health")
async def health():
    """Health check endpoint."""
    gemini = bool(os.getenv("GEMINI_API_KEY", "")) and os.getenv("GEMINI_API_KEY") != "your_gemini_api_key_here"
    exa = bool(os.getenv("EXA_API_KEY", "")) and os.getenv("EXA_API_KEY") != "your_exa_api_key_here"
    return {"status": "ok", "gemini_configured": gemini, "exa_configured": exa}


@app.get("/")
async def root():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("web.app:app", host="0.0.0.0", port=8000, reload=True)
