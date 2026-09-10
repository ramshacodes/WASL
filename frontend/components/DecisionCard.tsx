"use client";

import { AgentDecision } from "@/lib/types";

export default function DecisionCard({ decision }: { decision: AgentDecision }) {
  return (
    <section className="animate-fadeUp rounded-2xl border border-gold-500/30 bg-navy-800/60 p-6 shadow-card">
      <p className="text-xs font-medium uppercase tracking-[0.14em] text-gold-400">Agent Decision</p>
      <p className="mt-2 font-display text-xl text-ivory">Transition confirmed</p>

      <div className="mt-3 flex items-center gap-2 text-sm text-mute">
        <span>Destination:</span>
        <span className="text-ivory">{decision.destination_flag} {decision.destination_country}</span>
        <span className="text-navy-600">·</span>
        <span>{decision.context}</span>
      </div>

      <p className="mt-4 text-xs uppercase tracking-wide text-mute">Selected assistance</p>
      <div className="mt-2 flex flex-wrap gap-2">
        {decision.selected_assistance.map((item) => (
          <span
            key={item}
            className="rounded-full border border-navy-600 bg-navy-900/60 px-3 py-1 text-xs text-ivory"
          >
            ✓ {item}
          </span>
        ))}
      </div>
    </section>
  );
}
