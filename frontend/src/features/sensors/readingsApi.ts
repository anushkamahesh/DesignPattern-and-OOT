const BASE: string = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

export interface Reading {
  device_id: string;
  value: number;
  unit: string;
  source: string;
  recorded_at: string;
}

export interface SamplingUpdate {
  sampling_interval_seconds: number;
  tracking_enabled: boolean;
}

export interface SamplingResponse {
  id: string;
  sampling_interval_seconds: number;
  tracking_enabled: boolean;
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

export const readSensor = (deviceId: string) =>
  request<Reading>(`/api/sensors/${deviceId}/read`, { method: "POST" });

export const getReadings = (deviceId: string, limit = 1) =>
  request<Reading[]>(`/api/sensors/${deviceId}/readings?limit=${limit}`);

export const updateSampling = (deviceId: string, body: SamplingUpdate) =>
  request<SamplingResponse>(`/api/devices/${deviceId}/sampling`, {
    method: "PATCH",
    body: JSON.stringify(body),
  });