"use client";

import { useState } from "react";
import { ToolCallResult } from "@/lib/types";

const STATUS_LABEL: Record<string, string> = {
  success: "✓ Success",
  not_required: "— Not required",
  error: "✕ Error",
};

export default function ApiActivityDrawer({ activity }: { activity: ToolCallResult[] }) {
  const [open, setOpen] = useState(false);

  return (
    <section className="rounded-2xl border border-navy-700 bg-navy-800/60 shadow-card">
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center justify-between px-6 py-4"
      >
        <div className="flex items-center gap-2">
          <h2 className="font-display text-lg text-ivory">API Activity</h2>
          <span className="text-xs text-mute">CAMARA / Network Tools</span>
        </div>
        <span className="text-mute transition-transform" style={{ transform: open ? "rotate(180deg)" : "none" }}>
          ⌄
        </span>
      </button>

      {open && (
        <div className="grid grid-cols-1 gap-3 border-t border-navy-700 px-6 py-5 sm:grid-cols-2">
          {activity.length === 0 && (
            <p className="text-sm text-mute">No tool calls yet.</p>
          )}
          {activity.map((t) => (
            <div key={t.tool} className="animate-fadeUp rounded-xl border border-navy-600 bg-navy-900/60 p-4">
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium text-ivory">{t.tool}</p>
                <span className="text-[11px] text-mute">{t.source === "live_api" ? "Live" : "Sandbox"}</span>
              </div>
              <p className={`mt-1 text-sm ${t.status === "success" ? "text-success" : "text-mute"}`}>
                {STATUS_LABEL[t.status] ?? t.status}
              </p>
              <p className="mt-1 text-xs text-mute">Result: {t.result}</p>
              <p className="mt-1 text-[11px] text-mute/70">
                Selected by agent: {t.selected_by_agent ? "Yes" : "No"}
              </p>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
