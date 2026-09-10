export type DemoPhase = "idle" | "transitioning" | "complete";

export interface Destination {
  country: string;
  flag: string;
}

export const DESTINATIONS: Destination[] = [
  { country: "Saudi Arabia", flag: "🇸🇦" },
  { country: "United Arab Emirates", flag: "🇦🇪" },
  { country: "Qatar", flag: "🇶🇦" },
  { country: "Bahrain", flag: "🇧🇭" },
  { country: "Oman", flag: "🇴🇲" },
  { country: "Türkiye", flag: "🇹🇷" },
];

export type WorkflowEventKind = "status" | "tool_call" | "tool_result" | "decision" | "briefing";
export type ToolStatus = "running" | "success" | "not_required" | "error";

export interface WorkflowEvent {
  step: number;
  node: string;
  kind: WorkflowEventKind;
  label: string;
  detail?: string | null;
  tool?: string | null;
  status: ToolStatus;
  timestamp: string;
}

export interface ToolCallResult {
  tool: string;
  status: "success" | "not_required" | "error";
  result: string;
  detail: Record<string, unknown>;
  selected_by_agent: boolean;
  source: "live_api" | "demo_cache";
}

export interface AgentDecision {
  transition_confirmed: boolean;
  destination_country: string;
  destination_flag: string;
  context: string;
  selected_assistance: string[];
}

export interface BriefingCard {
  category: string;
  icon: string;
  title: string;
  content: string;
}

export interface TransitionResponse {
  request_id: string;
  demo_mode: boolean;
  events: WorkflowEvent[];
  tool_activity: ToolCallResult[];
  decision: AgentDecision;
  briefing: BriefingCard[];
}
