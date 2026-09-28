import { useCallback, useEffect, useState } from "react";
import { getLocationConfig, listLocations, listZoneDevices } from "./locationsApi";

export interface ZoneOption {
  zoneId: string;
  label: string; // "{location name} - {zone name}"
}

export interface ZoneGroup {
  locationId: string;
  locationName: string;
  zones: ZoneOption[];
}

// Loads every saved location's zones (for the picker) and which zone each
// device is in. Pass a changing refreshKey to reload after config changes.
export function useZoneAssignments(refreshKey = 0) {
  const [groups, setGroups] = useState<ZoneGroup[]>([]);
  const [zoneByDevice, setZoneByDevice] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    try {
      const locations = await listLocations();
      const configs = await Promise.all(locations.map((l) => getLocationConfig(l.id)));
      const nextGroups: ZoneGroup[] = configs.map((c) => ({
        locationId: c.location.id,
        locationName: c.location.name,
        zones: c.zones.map((z) => ({
          zoneId: z.id,
          label: `${c.location.name} \u2014 ${z.name}`,
        })),
      }));
      const memberships = await Promise.all(
        configs.flatMap((c) =>
          c.zones.map(async (z) => ({
            zoneId: z.id,
            devices: await listZoneDevices(c.location.id, z.id),
          })),
        ),
      );
      const map: Record<string, string> = {};
      for (const m of memberships) {
        for (const d of m.devices) map[d.id] = m.zoneId;
      }
      setGroups(nextGroups);
      setZoneByDevice(map);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not load zones.");
    }
  }, []);

  useEffect(() => {
    void reload();
  }, [reload, refreshKey]);

  return { groups, zoneByDevice, error, reload };
}