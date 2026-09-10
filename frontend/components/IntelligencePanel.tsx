"use client";

import { WorkflowEvent } from "@/lib/types";

const KIND_STYLES: Record<string, { dot: string; label: string }> = {
  status: { dot: "bg-mute", label: "text-mute" },
  tool_call: { dot: "bg-gold-400 animate-pulseDot", label: "text-gold-300" },
  tool_result: { dot: "bg-success", label: "text-ivory" },
  decision: { dot: "bg-gold-500", label: "text-gold-300" },
  briefing: { dot: "bg-success", label: "text-ivory" },
};

export default function IntelligencePanel({ events }: { events: WorkflowEvent[] }) {
  return (
    <section className="rounded-2xl border border-navy-700 bg-navy-800/60 p-6 shadow-card">
      <div className="flex items-center justify-between">
        <h2 className="font-display text-lg text-ivory">WASL Intelligence</h2>
        {events.length === 0 && <span className="text-xs text-mute">Idle</span>}
      </div>

      <div className="wasl-scroll mt-4 max-h-[340px] space-y-3 overflow-y-auto pr-1">
        {events.length === 0 && (
          <p className="py-8 text-center text-sm text-mute">
            Waiting for a network signal — click Simulate Border Transition to begin.
          </p>
        )}

        {events.map((e) => {
          const style = KIND_STYLES[e.kind] ?? KIND_STYLES.status;
          return (
            <div key={e.step} className="flex animate-fadeUp items-start gap-3">
              <div className="mt-1.5 flex h-full flex-col items-center">
                <span className={`h-2 w-2 shrink-0 rounded-full ${style.dot}`} />
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-baseline gap-2">
                  <p className={`text-sm font-medium ${style.label}`}>{e.label}</p>
                  {e.tool && (
                    <span className="rounded-full border border-navy-600 px-2 py-0.5 text-[10px] uppercase tracking-wide text-mute">
                      {e.tool} · CAMARA
                    </span>
                  )}
                </div>
                {e.detail && <p className="mt-0.5 text-xs text-mute">{e.detail}</p>}
              </div>
              <span className="shrink-0 font-mono text-[11px] text-mute/60">{e.timestamp}</span>
            </div>
          );
        })}
      </div>
    </section>
  );
}
