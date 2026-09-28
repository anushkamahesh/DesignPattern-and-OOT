const BASE: string = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

export interface LocationSummary {
  id: string;
  name: string;
}

export interface Zone {
  id: string;
  location_id: string;
  name: string;
  moisture_threshold_low: number;
  moisture_threshold_high: number;
  schedule: Record<string, unknown>;
}

export interface LocationConfig {
  location: LocationSummary;
  zones: Zone[];
}

export interface ZoneInput {
  name: string;
  moisture_threshold_low: number;
  moisture_threshold_high: number;
  schedule?: Record<string, unknown>;
}

export interface ZoneDevice {
  id: string;
  device_type: string;
  role: string;
  display_name: string | null;
  device_family: string;
  zone_id: string | null;
  location_id: string | null;
}

export interface DeviceZone {
  id: string;
  zone_id: string | null;
  location_id: string | null;
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
      if (typeof body.detail === "string") {
        message = body.detail;
      } else if (Array.isArray(body.detail)) {
        message = body.detail
          .map((d: { msg?: string }) => d.msg ?? "invalid value")
          .join("; ");
      }
    } catch {
      /* keep default message */
    }
    throw new ApiError(res.status, message);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export const listLocations = () => request<LocationSummary[]>("/api/locations");

export const getLocationConfig = (id: string) =>
  request<LocationConfig>(`/api/locations/${id}/config`);

export const createLocationConfig = (location_name: string, zones: ZoneInput[]) =>
  request<LocationConfig>("/api/locations/config", {
    method: "POST",
    body: JSON.stringify({ location_name, zones }),
  });

export const deleteLocation = (id: string) =>
  request<void>(`/api/locations/${id}`, { method: "DELETE" });

export const addZone = (locationId: string, zone: ZoneInput) =>
  request<Zone>(`/api/locations/${locationId}/zones`, {
    method: "POST",
    body: JSON.stringify(zone),
  });

export const updateZone = (locationId: string, zoneId: string, zone: ZoneInput) =>
  request<Zone>(`/api/locations/${locationId}/zones/${zoneId}`, {
    method: "PATCH",
    body: JSON.stringify(zone),
  });

export const deleteZone = (locationId: string, zoneId: string) =>
  request<void>(`/api/locations/${locationId}/zones/${zoneId}`, { method: "DELETE" });

export const listZoneDevices = (locationId: string, zoneId: string) =>
  request<ZoneDevice[]>(`/api/locations/${locationId}/zones/${zoneId}/devices`);

export const assignDeviceZone = (deviceId: string, zoneId: string | null) =>
  request<DeviceZone>(`/api/devices/${deviceId}/zone`, {
    method: "PATCH",
    body: JSON.stringify({ zone_id: zoneId }),
  });