"use client";

import { DemoPhase, Destination, DESTINATIONS } from "@/lib/types";

interface Props {
  phase: DemoPhase;
  originCountry: string;
  originFlag: string;
  destination: Destination;
  onDestinationChange: (d: Destination) => void;
  locationVerified: boolean;
  onSimulate: () => void;
}

export default function JourneyCard({
  phase,
  originCountry,
  originFlag,
  destination,
  onDestinationChange,
  locationVerified,
  onSimulate,
}: Props) {
  const currentCountry = locationVerified ? `${destination.country} ${destination.flag}` : `${originCountry} ${originFlag}`;
  const travelStatus = phase === "idle" ? "Monitoring" : locationVerified ? "Transition confirmed" : "Evaluating transition";
  const locked = phase !== "idle";

  return (
    <section className="rounded-2xl border border-navy-700 bg-navy-800/60 p-6 shadow-card">
      <p className="text-xs font-medium uppercase tracking-[0.14em] text-mute">Current Journey</p>

      <div className="mt-4 flex items-center justify-center gap-6">
        <div className={`flex flex-col items-center gap-1 transition-opacity duration-500 ${locationVerified ? "opacity-40" : "opacity-100"}`}>
          <span className="text-4xl">{originFlag}</span>
          <span className="text-sm text-mute">{originCountry}</span>
        </div>

        <div className="relative h-px w-24 bg-navy-600">
          {phase !== "idle" && (
            <span className="absolute inset-0 origin-left animate-signal bg-gradient-to-r from-gold-500 to-gold-300" />
          )}
        </div>

        <div className={`flex flex-col items-center gap-1 transition-opacity duration-500 ${locationVerified ? "opacity-100" : "opacity-40"}`}>
          <span className="text-4xl">{destination.flag}</span>
          <span className="text-sm text-mute">{destination.country}</span>
        </div>
      </div>

      <label className="mt-5 block">
        <span className="text-xs font-medium uppercase tracking-[0.1em] text-mute">Destination</span>
        <select
          value={destination.country}
          disabled={locked}
          onChange={(e) => {
            const next = DESTINATIONS.find((d) => d.country === e.target.value);
            if (next) onDestinationChange(next);
          }}
          className="mt-1.5 w-full rounded-lg border border-navy-600 bg-navy-900/60 px-3 py-2 text-sm text-ivory disabled:cursor-not-allowed disabled:opacity-60"
        >
          {DESTINATIONS.map((d) => (
            <option key={d.country} value={d.country}>
              {d.flag} {d.country}
            </option>
          ))}
        </select>
      </label>

      <dl className="mt-6 grid grid-cols-2 gap-x-4 gap-y-2.5 border-t border-navy-700 pt-4 text-sm">
        <Row label="Current Country" value={currentCountry} />
        <Row label="Network" value="Connected" />
        <Row label="Device" value="Active" />
        <Row label="Travel Status" value={travelStatus} />
      </dl>

      <button
        onClick={onSimulate}
        disabled={phase === "transitioning"}
        className="mt-6 w-full rounded-xl bg-gold-500 py-3.5 font-medium tracking-wide text-navy-950 transition hover:bg-gold-400 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {phase === "idle" && "Simulate Border Transition"}
        {phase === "transitioning" && "Transition in progress…"}
        {phase === "complete" && "Run Simulation Again"}
      </button>
    </section>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <>
      <dt className="text-mute">{label}</dt>
      <dd className="text-right font-medium text-ivory">{value}</dd>
    </>
  );
}
