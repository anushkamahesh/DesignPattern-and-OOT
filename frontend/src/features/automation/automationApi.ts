const BASE: string = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

export interface ZoneRecommendation {
  zone_id: string;
  zone_name: string;
  latest_moisture: number | null;
  action: string;
  reason: string;
  score: number | null;
}

export interface Evaluation {
  location_id: string;
  strategy_key: string;
  recommendations: ZoneRecommendation[];
}

export interface AutomationRule {
  location_id: string;
  strategy_key: string | null;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    let message = `Request failed (${res.status})`;
    try {
      const body = await res.json();
      if (typeof body.detail === "string") message = body.detail;
    } catch {
      /* keep default message */
    }
    throw new ApiError(res.status, message);
  }
  return (await res.json()) as T;
}

export const listStrategies = () => request<string[]>("/api/automation/strategies");

export const getRule = (locationId: string) =>
  request<AutomationRule>(`/api/locations/${locationId}/automation`);

export const saveRule = (locationId: string, strategy_key: string) =>
  request<AutomationRule>(`/api/locations/${locationId}/automation`, {
    method: "PUT",
    body: JSON.stringify({ strategy_key }),
  });

export const evaluateLocation = (locationId: string) =>
  request<Evaluation>(`/api/locations/${locationId}/automation/evaluate`, {
    method: "POST",
  });