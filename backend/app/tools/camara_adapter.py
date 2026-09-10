"""
CAMARA / Nokia Network as Code tool adapter.

Every function below exposes the SAME interface regardless of whether we are
hitting a live sandbox or returning a deterministic demo response. This is the
seam the agent talks to — it never knows (or cares) which branch executed.

Set DEMO_MODE=false and provide the relevant NOKIA_* / CAMARA_* env vars to
attempt live calls. If a live call fails for any reason, we log it and fall
back to the demo response rather than breaking the workflow — a broken demo
is worse than a clearly-labeled cached one.
"""
from __future__ import annotations

import os
import httpx
from app.models import ToolCallResult

DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"
CAMARA_BASE_URL = os.getenv("CAMARA_BASE_URL", "")
CAMARA_API_KEY = os.getenv("CAMARA_API_KEY", "")


# ---------------------------------------------------------------------------
# Deterministic demo responses. verify_location is dynamic (keyed off
# whichever destination the traveler picked) since WASL supports several
# MENA corridors, not just one fixed route. The rest are country-agnostic.
# These are hand-written to look like plausible CAMARA sandbox payloads, not
# real captured traffic. The README is explicit that this is cached data.
# ---------------------------------------------------------------------------
_COUNTRY_CODES = {
    "Saudi Arabia": "SA",
    "United Arab Emirates": "AE",
    "Qatar": "QA",
    "Bahrain": "BH",
    "Oman": "OM",
    "Türkiye": "TR",
    "Kuwait": "KW",
}

_DEMO_RESPONSES = {
    "get_device_status": {
        "result": "Device active on network",
        "detail": {"connectivityStatus": "CONNECTED_DATA", "roaming": True},
    },
    "check_geofence": {
        "result": "No geofence configured for this journey",
        "detail": {"geofenceConfigured": False},
    },
    "check_network_quality": {
        "result": "Standard QoS profile sufficient",
        "detail": {"qosProfile": "QOS_L", "recommended": False},
    },
}


async def _call_live(endpoint: str, payload: dict) -> dict | None:
    """Attempt a real CAMARA sandbox call. Returns None on any failure."""
    if not CAMARA_BASE_URL or not CAMARA_API_KEY:
        return None
    try:
        async with httpx.AsyncClient(timeout=6.0) as client:
            resp = await client.post(
                f"{CAMARA_BASE_URL}/{endpoint}",
                json=payload,
                headers={"Authorization": f"Bearer {CAMARA_API_KEY}"},
            )
            resp.raise_for_status()
            return resp.json()
    except Exception:
        return None


async def verify_location(device_id: str, destination_country: str) -> ToolCallResult:
    live = None if DEMO_MODE else await _call_live(
        "location-verification/v1/verify",
        {"device": {"phoneNumber": device_id}, "country": destination_country},
    )
    if live:
        return ToolCallResult(
            tool="Location Verification",
            status="success",
            result=live.get("country", destination_country),
            detail=live,
            source="live_api",
        )
    country_code = _COUNTRY_CODES.get(destination_country, "XX")
    return ToolCallResult(
        tool="Location Verification",
        status="success",
        result=destination_country,
        detail={"country": country_code, "verificationResult": "TRUE", "matchType": "COUNTRY"},
        source="demo_cache",
    )


async def get_device_status(device_id: str) -> ToolCallResult:
    live = None if DEMO_MODE else await _call_live(
        "device-status/v1/connectivity", {"device": {"phoneNumber": device_id}}
    )
    if live:
        return ToolCallResult(
            tool="Device Status",
            status="success",
            result=live.get("connectivityStatus", "Active"),
            detail=live,
            source="live_api",
        )
    demo = _DEMO_RESPONSES["get_device_status"]
    return ToolCallResult(
        tool="Device Status",
        status="success",
        result=demo["result"],
        detail=demo["detail"],
        source="demo_cache",
    )


async def check_geofence(device_id: str) -> ToolCallResult:
    # Not required for this scenario — surfaced so the UI can show the agent
    # deliberately skipping a tool, not just calling everything available.
    demo = _DEMO_RESPONSES["check_geofence"]
    return ToolCallResult(
        tool="Geofencing",
        status="not_required",
        result=demo["result"],
        detail=demo["detail"],
        selected_by_agent=False,
        source="demo_cache",
    )


async def check_network_quality(device_id: str) -> ToolCallResult:
    live = None if DEMO_MODE else await _call_live(
        "quality-on-demand/v1/sessions", {"device": {"phoneNumber": device_id}}
    )
    if live:
        return ToolCallResult(
            tool="Quality on Demand",
            status="success",
            result=live.get("qosProfile", "Standard"),
            detail=live,
            source="live_api",
        )
    demo = _DEMO_RESPONSES["check_network_quality"]
    return ToolCallResult(
        tool="Quality on Demand",
        status="success",
        result=demo["result"],
        detail=demo["detail"],
        source="demo_cache",
    )
