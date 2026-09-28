import { useState } from "react";
import { assignDeviceZone } from "./locationsApi";
import type { ZoneGroup } from "./useZoneAssignments";

interface Props {
  deviceId: string;
  groups: ZoneGroup[];
  value: string | null; // current zone id, or null when unassigned
  onChanged?: () => void;
}

export default function ZonePicker({ deviceId, groups, value, onChanged }: Props) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleChange(next: string) {
    setBusy(true);
    setError(null);
    try {
      await assignDeviceZone(deviceId, next === "" ? null : next);
      onChanged?.();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not update zone.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="text-sm">
      <label className="block text-xs text-gray-600">
        Zone
        <select
          className="mt-1 w-full rounded border border-gray-300 px-2 py-1 text-sm"
          value={value ?? ""}
          disabled={busy}
          onChange={(e) => handleChange(e.target.value)}
        >
          <option value="">Unassigned</option>
          {groups.map((g) => (
            <optgroup key={g.locationId} label={g.locationName}>
              {g.zones.map((z) => (
                <option key={z.zoneId} value={z.zoneId}>
                  {z.label}
                </option>
              ))}
            </optgroup>
          ))}
        </select>
      </label>
      {error && <p role="alert" className="mt-1 text-xs text-red-700">{error}</p>}
    </div>
  );
}