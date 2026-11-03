const BASE: string = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

export interface OverviewDevice {
  id: string;
  device_type: string;
  role: string;
  display_name: string | null;
}

export interface OverviewReading {
  device_id: string;
  value: number;
  unit: string;
  recorded_at: string;
  tracking_enabled: boolean;
  sampling_interval_seconds: number;
}

export interface OverviewZone {
  id: string;
  name: string;
  moisture_threshold_low: number;
  moisture_threshold_high: number;
  devices: OverviewDevice[];
  latest_readings: OverviewReading[];
}

export interface LocationOverview {
  location: { id: string; name: string };
  device_counts: { sensor: number; actuator: number };
  zones: OverviewZone[];
  strategy_key: string | null;
  last_recommendation: { action: string; reason: string } | null;
}

// The only call the overview panel makes: one request, one snapshot.
export async function getOverview(locationId: string): Promise<LocationOverview> {
  const res = await fetch(`${BASE}/api/locations/${locationId}/overview`);
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
  return (await res.json()) as LocationOverview;
}