import type { Zone, ZoneInput } from "./locationsApi";

export interface ZoneForm {
  name: string;
  low: string;
  high: string;
  schedule: string;
}

export const emptyZoneForm = (): ZoneForm => ({
  name: "",
  low: "0.2",
  high: "0.6",
  schedule: "",
});

export const zoneToForm = (z: Zone): ZoneForm => ({
  name: z.name,
  low: String(z.moisture_threshold_low),
  high: String(z.moisture_threshold_high),
  schedule: Object.keys(z.schedule ?? {}).length ? JSON.stringify(z.schedule) : "",
});

// Client-side mirror of the server rules; the API remains the authority.
export function parseZoneForm(f: ZoneForm): { value?: ZoneInput; error?: string } {
  const name = f.name.trim();
  if (!name) return { error: "Zone name is required." };

  const low = Number(f.low);
  const high = Number(f.high);
  if (f.low.trim() === "" || f.high.trim() === "" || Number.isNaN(low) || Number.isNaN(high)) {
    return { error: "Thresholds must be numbers." };
  }
  if (low < 0 || low > 1 || high < 0 || high > 1) {
    return { error: "Thresholds must be between 0 and 1." };
  }
  if (low >= high) {
    return { error: "Low threshold must be less than high threshold." };
  }

  let schedule: Record<string, unknown> = {};
  if (f.schedule.trim()) {
    try {
      const parsed: unknown = JSON.parse(f.schedule);
      if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) {
        return { error: 'Schedule must be a JSON object, e.g. {"start":"06:00"}.' };
      }
      schedule = parsed as Record<string, unknown>;
    } catch {
      return { error: "Schedule is not valid JSON." };
    }
  }

  return {
    value: {
      name,
      moisture_threshold_low: low,
      moisture_threshold_high: high,
      schedule,
    },
  };
}