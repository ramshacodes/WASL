"""Pydantic models shared across the WASL backend."""
from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field


class TransitionRequest(BaseModel):
    """Payload the frontend sends when the traveler simulates a border transition."""
    origin_country: str = Field(default="Kuwait")
    origin_flag: str = Field(default="🇰🇼")
    destination_country: str = Field(default="Saudi Arabia")
    destination_flag: str = Field(default="🇸🇦")
    device_id: str = Field(default="demo-device-001")


class ToolCallResult(BaseModel):
    """Normalized result returned by every CAMARA tool adapter call."""
    tool: str
    status: Literal["success", "not_required", "error"]
    result: str
    detail: dict[str, Any] = Field(default_factory=dict)
    selected_by_agent: bool = True
    source: Literal["live_api", "demo_cache"] = "demo_cache"


class WorkflowEvent(BaseModel):
    """A single line item shown in the WASL Intelligence panel."""
    step: int
    node: str
    kind: Literal["status", "tool_call", "tool_result", "decision", "briefing"]
    label: str
    detail: str | None = None
    tool: str | None = None
    status: Literal["running", "success", "not_required", "error"] = "success"
    timestamp: str


class BriefingCard(BaseModel):
    category: str
    icon: str
    title: str
    content: str


class AgentDecision(BaseModel):
    transition_confirmed: bool
    destination_country: str
    destination_flag: str
    context: str
    selected_assistance: list[str]


class TransitionResponse(BaseModel):
    request_id: str
    demo_mode: bool
    events: list[WorkflowEvent]
    tool_activity: list[ToolCallResult]
    decision: AgentDecision
    briefing: list[BriefingCard]
