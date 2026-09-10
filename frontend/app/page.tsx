"use client";

import { useCallback, useRef, useState } from "react";
import Header from "@/components/Header";
import JourneyCard from "@/components/JourneyCard";
import IntelligencePanel from "@/components/IntelligencePanel";
import ApiActivityDrawer from "@/components/ApiActivityDrawer";
import DecisionCard from "@/components/DecisionCard";
import BriefingGrid from "@/components/BriefingGrid";
import { simulateTransition } from "@/lib/api";
import { DemoPhase, TransitionResponse, WorkflowEvent, Destination, DESTINATIONS } from "@/lib/types";

const EVENT_REVEAL_DELAY_MS = 420;
const POST_EVENTS_PAUSE_MS = 500;

export default function Home() {
  const [phase, setPhase] = useState<DemoPhase>("idle");
  const [destination, setDestination] = useState<Destination>(DESTINATIONS[0]);
  const [response, setResponse] = useState<TransitionResponse | null>(null);
  const [visibleEvents, setVisibleEvents] = useState<WorkflowEvent[]>([]);
  const [showDecision, setShowDecision] = useState(false);
  const [showBriefing, setShowBriefing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const timers = useRef<ReturnType<typeof setTimeout>[]>([]);

  const clearTimers = () => {
    timers.current.forEach(clearTimeout);
    timers.current = [];
  };

  const handleSimulate = useCallback(async () => {
    clearTimers();
    setError(null);
    setPhase("transitioning");
    setResponse(null);
    setVisibleEvents([]);
    setShowDecision(false);
    setShowBriefing(false);

    try {
      const data = await simulateTransition(destination);
      setResponse(data);

      data.events.forEach((event, i) => {
        const t = setTimeout(() => {
          setVisibleEvents((prev) => [...prev, event]);
        }, i * EVENT_REVEAL_DELAY_MS);
        timers.current.push(t);
      });

      const afterEvents = data.events.length * EVENT_REVEAL_DELAY_MS + POST_EVENTS_PAUSE_MS;
      timers.current.push(
        setTimeout(() => setShowDecision(true), afterEvents)
      );
      timers.current.push(
        setTimeout(() => {
          setShowBriefing(true);
          setPhase("complete");
        }, afterEvents + 500)
      );
    } catch (e) {
      setError(
        "Couldn't reach the WASL backend. Make sure the FastAPI server is running on the configured API URL."
      );
      setPhase("idle");
    }
  }, [destination]);

  const locationVerified = visibleEvents.some(
    (e) => e.kind === "tool_result" && e.tool === "Location Verification"
  );

  return (
    <main className="mx-auto min-h-screen max-w-5xl px-6 py-8">
      <Header />

      <div className="mt-6 grid grid-cols-1 gap-5 lg:grid-cols-[320px_1fr]">
        <JourneyCard
          phase={phase}
          originCountry="Kuwait"
          originFlag="🇰🇼"
          destination={destination}
          onDestinationChange={setDestination}
          locationVerified={locationVerified}
          onSimulate={handleSimulate}
        />
        <IntelligencePanel events={visibleEvents} />
      </div>

      {error && (
        <p className="mt-4 rounded-xl border border-danger/30 bg-danger/10 px-4 py-3 text-sm text-danger">
          {error}
        </p>
      )}

      {response && (
        <div className="mt-5">
          <ApiActivityDrawer activity={response.tool_activity} />
        </div>
      )}

      {response && showDecision && (
        <div className="mt-5">
          <DecisionCard decision={response.decision} />
        </div>
      )}

      {response && showBriefing && (
        <div className="mt-5">
          <BriefingGrid cards={response.briefing} decision={response.decision} />
        </div>
      )}

      <footer className="mt-10 pb-6 text-center text-[11px] text-mute/60">
        CAMARA provides the signal. The agent provides the intelligence. WASL provides the experience.
        {response && !response.demo_mode ? " · Live CAMARA calls" : " · Demo sandbox data"}
      </footer>
    </main>
  );
}
