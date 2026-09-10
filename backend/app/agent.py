"""
WASL agent workflow.

receive_network_event -> analyze_transition -> verify_location ->
check_device_context -> evaluate_network_context -> analyze_traveler_context ->
select_relevant_assistance -> generate_briefing

Each node appends WorkflowEvent entries to state["events"] as it runs, so the
final state carries a complete, ordered timeline the frontend can play back
sequentially (no streaming infra required — reliability over cleverness,
per the hackathon brief). Each node also appends any ToolCallResult it
produced to state["tool_activity"] for the API Activity panel.
"""
from __future__ import annotations

import os
import json
from datetime import datetime, timezone
from typing import TypedDict, Any

from langgraph.graph import StateGraph, END

from app.tools import camara_adapter as camara
from app.models import WorkflowEvent, ToolCallResult, AgentDecision, BriefingCard

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")


class AgentState(TypedDict, total=False):
    origin_country: str
    origin_flag: str
    destination_country: str
    destination_flag: str
    device_id: str
    step: int
    events: list[dict]
    tool_activity: list[dict]
    location_result: dict
    device_result: dict
    network_result: dict
    geofence_result: dict
    selected_assistance: list[str]
    briefing: list[dict]


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%H:%M:%S")


def _emit(state: AgentState, node: str, kind: str, label: str,
          detail: str | None = None, tool: str | None = None,
          status: str = "success") -> AgentState:
    step = state.get("step", 0) + 1
    events = list(state.get("events", []))
    events.append(WorkflowEvent(
        step=step, node=node, kind=kind, label=label, detail=detail,
        tool=tool, status=status, timestamp=_now(),
    ).model_dump())
    return {**state, "step": step, "events": events}


def _add_tool_activity(state: AgentState, result: ToolCallResult) -> AgentState:
    activity = list(state.get("tool_activity", []))
    activity.append(result.model_dump())
    return {**state, "tool_activity": activity}


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------

def receive_network_event(state: AgentState) -> AgentState:
    state = _emit(state, "receive_network_event", "status",
                  "Monitoring network context")
    state = _emit(state, "receive_network_event", "status",
                  "Potential transition detected",
                  detail=f"{state['origin_country']} → {state['destination_country']}")
    return state


def analyze_transition(state: AgentState) -> AgentState:
    return _emit(state, "analyze_transition", "decision",
                 "Evaluating which network tools are needed",
                 detail="Location Verification, Device Status, Quality on Demand selected")


async def verify_location(state: AgentState) -> AgentState:
    state = _emit(state, "verify_location", "tool_call",
                  "Calling CAMARA Location Verification…",
                  tool="Location Verification", status="running")
    result = await camara.verify_location(state["device_id"], state["destination_country"])
    state = {**state, "location_result": result.model_dump()}
    state = _add_tool_activity(state, result)
    state = _emit(state, "verify_location", "tool_result",
                  f"Location verified — {result.result}",
                  tool="Location Verification", status="success")
    return state


async def check_device_context(state: AgentState) -> AgentState:
    state = _emit(state, "check_device_context", "tool_call",
                  "Checking device state…", tool="Device Status", status="running")
    result = await camara.get_device_status(state["device_id"])
    state = {**state, "device_result": result.model_dump()}
    state = _add_tool_activity(state, result)
    state = _emit(state, "check_device_context", "tool_result",
                  f"Device active — {result.result}",
                  tool="Device Status", status="success")
    return state


async def evaluate_network_context(state: AgentState) -> AgentState:
    # Quality on Demand — actively evaluated
    state = _emit(state, "evaluate_network_context", "tool_call",
                  "Evaluating connectivity quality…",
                  tool="Quality on Demand", status="running")
    qos_result = await camara.check_network_quality(state["device_id"])
    state = {**state, "network_result": qos_result.model_dump()}
    state = _add_tool_activity(state, qos_result)
    state = _emit(state, "evaluate_network_context", "tool_result",
                  f"Network context established — {qos_result.result}",
                  tool="Quality on Demand", status="success")

    # Geofencing — deliberately not needed for this journey; shown so the UI
    # proves the agent is selecting tools, not calling everything available.
    geofence_result = await camara.check_geofence(state["device_id"])
    state = {**state, "geofence_result": geofence_result.model_dump()}
    state = _add_tool_activity(state, geofence_result)
    state = _emit(state, "evaluate_network_context", "tool_result",
                  "Geofencing not required for this journey",
                  tool="Geofencing", status="not_required")
    return state


def analyze_traveler_context(state: AgentState) -> AgentState:
    return _emit(state, "analyze_traveler_context", "decision",
                 "Context established",
                 detail=f"Cross-border traveler now in {state['destination_country']}")


def select_relevant_assistance(state: AgentState) -> AgentState:
    # In a fuller build this would weigh device/network signals (e.g. skip
    # "Connectivity" if roaming data is already active). For this scenario
    # all six categories are relevant to a first-time cross-border traveler.
    selected = [
        "Connectivity", "Emergency", "Transportation",
        "Payments", "Local Services", "Attractions",
    ]
    state = {**state, "selected_assistance": selected}
    return _emit(state, "select_relevant_assistance", "decision",
                 "Transition verified — assistance categories selected",
                 detail=", ".join(selected))


async def generate_briefing(state: AgentState) -> AgentState:
    state = _emit(state, "generate_briefing", "status",
                  "Generating personalized briefing…", status="running")

    briefing = await _build_briefing(state)
    state = {**state, "briefing": [b.model_dump() for b in briefing]}
    state = _emit(state, "generate_briefing", "briefing",
                  "Personalized transition briefing ready")
    return state


# ---------------------------------------------------------------------------
# Briefing generation — Gemini if a key is configured, static fallback otherwise
# ---------------------------------------------------------------------------

_FALLBACK_BRIEFINGS: dict[str, list[BriefingCard]] = {
    "Saudi Arabia": [
        BriefingCard(category="connectivity", icon="📶", title="Connectivity",
                     content="Your Kuwait SIM roams onto STC/Mobily coverage in Saudi Arabia. "
                             "Enable data roaming or grab a local eSIM at the border for lower rates."),
        BriefingCard(category="emergency", icon="🚨", title="Emergency",
                     content="Dial 911 for police/ambulance/fire nationwide. Kuwait's embassy in "
                             "Riyadh can assist with consular emergencies."),
        BriefingCard(category="transportation", icon="🚕", title="Transportation",
                     content="Uber and Careem operate across major cities. The Haramain high-speed "
                             "rail connects Jeddah, Makkah, Madinah and Riyadh."),
        BriefingCard(category="payments", icon="💳", title="Payments",
                     content="Mada and Visa/Mastercard are widely accepted. Carry some cash (SAR) "
                             "for smaller vendors and taxis outside major cities."),
        BriefingCard(category="local_services", icon="🍽️", title="Nearby",
                     content="Halal dining is the default nationwide. Local chains like Najd "
                             "Village or Al Baik are a reliable first meal."),
        BriefingCard(category="explore", icon="📍", title="Explore",
                     content="Near the Eastern Province border crossing, Dammam's Corniche and "
                             "the historic Qatif old town are an easy first stop."),
        BriefingCard(category="local_context", icon="ℹ️", title="Local Context",
                     content="Dress modestly in public spaces. Friday is the primary weekly "
                             "holiday, and prayer times briefly pause business in most shops."),
    ],
    "United Arab Emirates": [
        BriefingCard(category="connectivity", icon="📶", title="Connectivity",
                     content="Etisalat and du cover the UAE well. A tourist eSIM or local prepaid "
                             "SIM is cheaper than roaming for stays over a couple of days."),
        BriefingCard(category="emergency", icon="🚨", title="Emergency",
                     content="Dial 999 for police, 998 for ambulance. Kuwait's embassy is in Abu Dhabi."),
        BriefingCard(category="transportation", icon="🚕", title="Transportation",
                     content="Careem and Uber are widely used. Dubai and Abu Dhabi metros are fast "
                             "and cheap for intra-city travel."),
        BriefingCard(category="payments", icon="💳", title="Payments",
                     content="Cards are accepted almost everywhere, including small vendors. "
                             "Apple Pay/Google Pay work at most terminals."),
        BriefingCard(category="local_services", icon="🍽️", title="Nearby",
                     content="Halal food is the norm; look for local favorites like Al Mallah or "
                             "Ravi Restaurant for a reliable first meal."),
        BriefingCard(category="explore", icon="📍", title="Explore",
                     content="If entering near Dubai, the Marina Walk or Old Dubai's Al Fahidi "
                             "district are easy first stops."),
        BriefingCard(category="local_context", icon="ℹ️", title="Local Context",
                     content="Dress modestly in public areas. Public displays of affection and "
                             "photographing people without consent are best avoided."),
    ],
    "Qatar": [
        BriefingCard(category="connectivity", icon="📶", title="Connectivity",
                     content="Ooredoo and Vodafone Qatar cover the country well; airport kiosks "
                             "sell tourist SIMs on arrival."),
        BriefingCard(category="emergency", icon="🚨", title="Emergency",
                     content="Dial 999 for police/ambulance/fire. Kuwait's embassy is in Doha."),
        BriefingCard(category="transportation", icon="🚕", title="Transportation",
                     content="Karwa taxis and Uber operate in Doha; the Doha Metro covers most "
                             "major districts cheaply."),
        BriefingCard(category="payments", icon="💳", title="Payments",
                     content="Cards are widely accepted in cities. Carry some cash (QAR) for "
                             "smaller vendors and souqs."),
        BriefingCard(category="local_services", icon="🍽️", title="Nearby",
                     content="Halal dining is standard nationwide. Souq Waqif is a reliable spot "
                             "for a first meal with plenty of variety."),
        BriefingCard(category="explore", icon="📍", title="Explore",
                     content="The Corniche and Museum of Islamic Art are easy, central first stops "
                             "in Doha."),
        BriefingCard(category="local_context", icon="ℹ️", title="Local Context",
                     content="Dress modestly in public spaces. Alcohol is restricted to licensed "
                             "hotel venues."),
    ],
    "Bahrain": [
        BriefingCard(category="connectivity", icon="📶", title="Connectivity",
                     content="Batelco, stc Bahrain and Zain cover the islands well; a tourist SIM "
                             "is available at Bahrain International Airport."),
        BriefingCard(category="emergency", icon="🚨", title="Emergency",
                     content="Dial 999 for police/ambulance/fire. Kuwait's embassy is in Manama."),
        BriefingCard(category="transportation", icon="🚕", title="Transportation",
                     content="Uber and Careem operate island-wide; Manama is compact enough for "
                             "short taxi hops between most sights."),
        BriefingCard(category="payments", icon="💳", title="Payments",
                     content="Cards are accepted broadly. Carry some cash (BHD) for the souqs and "
                             "smaller cafes."),
        BriefingCard(category="local_services", icon="🍽️", title="Nearby",
                     content="Halal dining is standard. Manama Souq is a good first stop for food "
                             "and local flavor."),
        BriefingCard(category="explore", icon="📍", title="Explore",
                     content="The Bahrain National Museum and Bahrain Fort are close to central "
                             "Manama and easy first stops."),
        BriefingCard(category="local_context", icon="ℹ️", title="Local Context",
                     content="Dress modestly in public spaces. Friday is the primary weekly holiday."),
    ],
    "Oman": [
        BriefingCard(category="connectivity", icon="📶", title="Connectivity",
                     content="Omantel and Ooredoo Oman cover main routes and cities; a tourist SIM "
                             "is easy to grab at Muscat airport."),
        BriefingCard(category="emergency", icon="🚨", title="Emergency",
                     content="Dial 9999 for police/ambulance/fire. Kuwait's embassy is in Muscat."),
        BriefingCard(category="transportation", icon="🚕", title="Transportation",
                     content="Ride-hailing coverage is thinner outside Muscat — renting a car is "
                             "common for exploring beyond the capital."),
        BriefingCard(category="payments", icon="💳", title="Payments",
                     content="Cards work in cities; carry cash (OMR) for rural areas, souqs and "
                             "smaller towns."),
        BriefingCard(category="local_services", icon="🍽️", title="Nearby",
                     content="Halal dining is standard nationwide. Mutrah Souq in Muscat is a "
                             "reliable first stop for food."),
        BriefingCard(category="explore", icon="📍", title="Explore",
                     content="Mutrah Corniche and the Grand Mosque are easy, central first stops "
                             "if entering near Muscat."),
        BriefingCard(category="local_context", icon="ℹ️", title="Local Context",
                     content="Dress modestly, especially outside major hotels. Public conduct "
                             "norms are conservative even by regional standards."),
    ],
    "Türkiye": [
        BriefingCard(category="connectivity", icon="📶", title="Connectivity",
                     content="Turkcell, Vodafone TR and Türk Telekom cover the country; a Turkcell "
                             "tourist SIM at the airport is the easiest option."),
        BriefingCard(category="emergency", icon="🚨", title="Emergency",
                     content="Dial 112 for all emergencies. Kuwait's embassy is in Ankara."),
        BriefingCard(category="transportation", icon="🚕", title="Transportation",
                     content="BiTaksi and Uber operate in major cities; Istanbul's metro and "
                             "ferries are fast and cheap once you have an Istanbulkart."),
        BriefingCard(category="payments", icon="💳", title="Payments",
                     content="Cards are widely accepted. Carry some cash (TRY) for smaller "
                             "vendors, markets and tips."),
        BriefingCard(category="local_services", icon="🍽️", title="Nearby",
                     content="Halal food is the norm nationwide. A local lokanta (family-run "
                             "eatery) is a reliable, affordable first meal."),
        BriefingCard(category="explore", icon="📍", title="Explore",
                     content="If entering near Istanbul, Sultanahmet's historic core is an easy, "
                             "walkable first stop."),
        BriefingCard(category="local_context", icon="ℹ️", title="Local Context",
                     content="Dress modestly when visiting mosques. Bargaining is expected and "
                             "welcomed in bazaars, not in fixed-price shops."),
    ],
}

_GENERIC_FALLBACK = [
    BriefingCard(category="connectivity", icon="📶", title="Connectivity",
                 content="Check with your carrier for roaming rates, or pick up a local eSIM on arrival."),
    BriefingCard(category="emergency", icon="🚨", title="Emergency",
                 content="Save the local emergency number and your embassy's contact as soon as you arrive."),
    BriefingCard(category="transportation", icon="🚕", title="Transportation",
                 content="Ride-hailing apps and local taxis are typically the easiest way to get around."),
    BriefingCard(category="payments", icon="💳", title="Payments",
                 content="Cards are usually accepted in cities; carry some local cash as backup."),
    BriefingCard(category="local_services", icon="🍽️", title="Nearby",
                 content="Ask your accommodation for a well-reviewed, nearby spot for your first meal."),
    BriefingCard(category="explore", icon="📍", title="Explore",
                 content="A central, walkable landmark is usually the easiest first stop after arrival."),
    BriefingCard(category="local_context", icon="ℹ️", title="Local Context",
                 content="Check local dress and conduct norms before heading out in public."),
]


async def _build_briefing(state: AgentState) -> list[BriefingCard]:
    fallback = _FALLBACK_BRIEFINGS.get(state["destination_country"], _GENERIC_FALLBACK)
    if not GEMINI_API_KEY:
        return fallback
    try:
        import httpx
        prompt = (
            "You are WASL, a proactive cross-border travel assistant. A traveler just "
            f"crossed from {state['origin_country']} into {state['destination_country']}. "
            "Write a short, genuinely useful personalized briefing as a JSON array of exactly "
            "7 objects, each with keys: category (one of connectivity, emergency, transportation, "
            "payments, local_services, explore, local_context), icon (a single emoji), title, "
            "and content (1-2 concise sentences, specific and practical, no fluff). "
            "Return ONLY the JSON array, no markdown fences, no preamble."
        )
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                "https://generativelanguage.googleapis.com/v1beta/models/"
                f"gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}",
                json={"contents": [{"parts": [{"text": prompt}]}]},
            )
            resp.raise_for_status()
            data = resp.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            text = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            parsed = json.loads(text)
            return [BriefingCard(**item) for item in parsed]
    except Exception:
        return fallback


# ---------------------------------------------------------------------------
# Graph assembly
# ---------------------------------------------------------------------------

def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("receive_network_event", receive_network_event)
    graph.add_node("analyze_transition", analyze_transition)
    graph.add_node("verify_location", verify_location)
    graph.add_node("check_device_context", check_device_context)
    graph.add_node("evaluate_network_context", evaluate_network_context)
    graph.add_node("analyze_traveler_context", analyze_traveler_context)
    graph.add_node("select_relevant_assistance", select_relevant_assistance)
    graph.add_node("generate_briefing", generate_briefing)

    graph.set_entry_point("receive_network_event")
    graph.add_edge("receive_network_event", "analyze_transition")
    graph.add_edge("analyze_transition", "verify_location")
    graph.add_edge("verify_location", "check_device_context")
    graph.add_edge("check_device_context", "evaluate_network_context")
    graph.add_edge("evaluate_network_context", "analyze_traveler_context")
    graph.add_edge("analyze_traveler_context", "select_relevant_assistance")
    graph.add_edge("select_relevant_assistance", "generate_briefing")
    graph.add_edge("generate_briefing", END)
    return graph.compile()


_compiled_graph = None


def get_graph():
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_graph()
    return _compiled_graph


async def run_transition_workflow(origin_country: str, origin_flag: str,
                                   destination_country: str, destination_flag: str,
                                   device_id: str) -> AgentState:
    graph = get_graph()
    initial_state: AgentState = {
        "origin_country": origin_country,
        "origin_flag": origin_flag,
        "destination_country": destination_country,
        "destination_flag": destination_flag,
        "device_id": device_id,
        "step": 0,
        "events": [],
        "tool_activity": [],
    }
    final_state = await graph.ainvoke(initial_state)
    return final_state
