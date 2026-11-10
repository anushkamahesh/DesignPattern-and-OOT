const BASE: string = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

export interface Actuator {
  id: string;
  device_type: string;
  role: string;
  display_name: string | null;
  device_family: string;
  zone_id: string | null;
  location_id: string | null;
  state: string;
  allowed_commands: string[];
  allowed_targets: string[];
}

export interface Execution {
  id: string;
  device_id: string;
  success: boolean;
  policy_applied: string[];
  message: string | null;
  created_at: string;
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

export const listActuators = () => request<Actuator[]>("/api/actuators");

export const transitionActuator = (deviceId: string, target: string) =>
  request<Actuator>(`/api/devices/${deviceId}/transition`, {
    method: "POST",
    body: JSON.stringify({ target }),
  });

export const listExecutions = (limit = 20) =>
  request<Execution[]>(`/api/actuators/executions?limit=${limit}`);

// Demo until Phase 10: apply a command through the decorated port.
export const applyCommand = (deviceId: string, command: string) =>
  request<Execution>(`/api/actuators/${deviceId}/apply`, {
    method: "POST",
    body: JSON.stringify({ command, payload: {} }),
  });