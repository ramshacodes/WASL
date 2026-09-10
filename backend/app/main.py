from __future__ import annotations

import os
import uuid

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.agent import run_transition_workflow
from app.models import (
    TransitionRequest, TransitionResponse, WorkflowEvent,
    ToolCallResult, AgentDecision, BriefingCard,
)

DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

app = FastAPI(title="WASL API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Last completed run, kept in memory so /api/agent/status has something to
# report without needing a database (out of scope per DO NOT BUILD list).
_last_run: dict | None = None


@app.get("/api/health")
async def health():
    return {
            "status": "ok",
            "demo_mode": DEMO_MODE,
            "gemini_key_present": bool(os.getenv("GEMINI_API_KEY")),
        }

@app.get("/api/debug/gemini")
async def debug_gemini():
    import httpx
    key = os.getenv("GEMINI_API_KEY", "")
    if not key:
        return {"error": "No key found"}
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                "https://generativelanguage.googleapis.com/v1beta/models/"
                f"gemini-flash-latest:generateContent?key={key}",
                json={"contents": [{"parts": [{"text": "Say hello in 5 words."}]}]},
            )
            return {
                "status_code": resp.status_code,
                "body": resp.text[:1000],
            }
    except Exception as e:
        return {"exception": str(e)}

@app.get("/api/debug/briefing")
async def debug_briefing():
    import httpx, json, os
    key = os.getenv("GEMINI_API_KEY", "")
    prompt = (
        "You are WASL, a proactive cross-border travel assistant. A traveler just "
        "crossed from Kuwait into Qatar. "
        "Write a short, genuinely useful personalized briefing as a JSON array of exactly "
        "7 objects, each with keys: category (one of connectivity, emergency, transportation, "
        "payments, local_services, explore, local_context), icon (a single emoji), title, "
        "and content (1-2 concise sentences, specific and practical, no fluff). "
        "Return ONLY the JSON array, no markdown fences, no preamble."
    )
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                "https://generativelanguage.googleapis.com/v1beta/models/"
                f"gemini-flash-latest:generateContent?key={key}",
                json={"contents": [{"parts": [{"text": prompt}]}]},
            )
            data = resp.json()
            raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
            cleaned = raw_text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            try:
                parsed = json.loads(cleaned)
                return {"stage": "parse_success", "parsed": parsed}
            except Exception as parse_err:
                return {"stage": "parse_failed", "error": str(parse_err), "raw_text": raw_text, "cleaned": cleaned}
    except Exception as e:
        return {"stage": "request_failed", "error": str(e)}
    
@app.get("/api/agent/status")
async def agent_status():
    if _last_run is None:
        return {"state": "idle"}
    return {"state": "complete", "request_id": _last_run["request_id"]}


@app.post("/api/demo/transition", response_model=TransitionResponse)
async def simulate_transition(payload: TransitionRequest):
    global _last_run

    try:
        final_state = await run_transition_workflow(
            origin_country=payload.origin_country,
            origin_flag=payload.origin_flag,
            destination_country=payload.destination_country,
            destination_flag=payload.destination_flag,
            device_id=payload.device_id,
        )
    except Exception as exc:  # pragma: no cover - safety net for the live demo
        raise HTTPException(status_code=500, detail=f"Agent workflow failed: {exc}")

    events = [WorkflowEvent(**e) for e in final_state.get("events", [])]
    tool_activity = [ToolCallResult(**t) for t in final_state.get("tool_activity", [])]
    briefing = [BriefingCard(**b) for b in final_state.get("briefing", [])]

    decision = AgentDecision(
        transition_confirmed=True,
        destination_country=payload.destination_country,
        destination_flag=payload.destination_flag,
        context="Cross-border traveler",
        selected_assistance=final_state.get("selected_assistance", []),
    )

    response = TransitionResponse(
        request_id=str(uuid.uuid4()),
        demo_mode=DEMO_MODE,
        events=events,
        tool_activity=tool_activity,
        decision=decision,
        briefing=briefing,
    )
    _last_run = response.model_dump()
    return response


@app.get("/api/demo/events")
async def last_events():
    """Convenience endpoint: replay the last transition's event timeline."""
    if _last_run is None:
        raise HTTPException(status_code=404, detail="No transition has been run yet.")
    return _last_run
