import { TransitionResponse, Destination } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export async function simulateTransition(destination: Destination): Promise<TransitionResponse> {
  const res = await fetch(`${API_BASE}/api/demo/transition`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      origin_country: "Kuwait",
      origin_flag: "🇰🇼",
      destination_country: destination.country,
      destination_flag: destination.flag,
      device_id: "demo-device-001",
    }),
  });

  if (!res.ok) {
    throw new Error(`Transition request failed: ${res.status}`);
  }

  return res.json();
}
