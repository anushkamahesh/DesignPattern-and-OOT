import { useCallback, useEffect, useRef, useState } from "react";
import { listLocations } from "../config/locationsApi";
import type { LocationSummary } from "../config/locationsApi";
import { getOverview } from "./overviewApi";
import type { LocationOverview, OverviewDevice, OverviewReading } from "./overviewApi";

const errMsg = (e: unknown) => (e instanceof Error ? e.message : "Something went wrong.");

function Card({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="rounded border border-gray-200 p-3">
      <p className="text-xs uppercase tracking-wide text-gray-500">{label}</p>
      <div className="mt-1 text-sm text-gray-900">{children}</div>
    </div>
  );
}

function DeviceLine({ device, reading }: { device: OverviewDevice; reading?: OverviewReading }) {
  return (
    <li className="rounded border border-gray-100 bg-gray-50 p-2 text-sm">
      <div className="flex items-center justify-between gap-2">
        <span className="font-medium">{device.display_name ?? device.device_type}</span>
        <span className="text-xs text-gray-500">
          {device.role} &middot; {device.device_type}
        </span>
      </div>
      {reading ? (
        <p className="mt-1 text-xs text-gray-700">
          {reading.value.toFixed(2)} {reading.unit} &middot; tracking{" "}
          {reading.tracking_enabled ? "on" : "off"} &middot; every {reading.sampling_interval_seconds} s
          <span className="text-gray-500"> &middot; {new Date(reading.recorded_at).toLocaleString()}</span>
        </p>
      ) : (
        <p className="mt-1 text-xs text-gray-500">No reading yet.</p>
      )}
    </li>
  );
}

export default function OverviewPanel({ refreshKey = 0 }: { refreshKey?: number }) {
  const [locations, setLocations] = useState<LocationSummary[]>([]);
  const [locationId, setLocationId] = useState("");
  const [overview, setOverview] = useState<LocationOverview | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const seq = useRef(0); // ignore responses from a location the user has already left

  // The dropdown list only. Changing config elsewhere does not refetch the overview.
  useEffect(() => {
    listLocations()
      .then((locs) => {
        setLocations(locs);
        setLocationId((current) => (locs.some((l) => l.id === current) ? current : ""));
      })
      .catch((e) => setError(errMsg(e)));
  }, [refreshKey]);

  const load = useCallback(async (id: string) => {
    const mine = ++seq.current;
    setLoading(true);
    setError(null);
    try {
      const data = await getOverview(id); // the single overview request
      if (mine === seq.current) setOverview(data);
    } catch (e) {
      if (mine === seq.current) {
        setOverview(null);
        setError(errMsg(e));
      }
    } finally {
      if (mine === seq.current) setLoading(false);
    }
  }, []);

  // Selecting a location performs exactly one overview fetch.
  useEffect(() => {
    if (!locationId) {
      seq.current++;
      setOverview(null);
      setError(null);
      setLoading(false);
      return;
    }
    void load(locationId);
  }, [locationId, load]);

  return (
    <section className="space-y-4 rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <h2 className="text-lg font-semibold text-gray-900">Overview</h2>
        <div className="flex items-end gap-2">
          <label className="text-xs text-gray-600">
            Location
            <select
              className="mt-1 block rounded border border-gray-300 px-2 py-1 text-sm"
              value={locationId}
              onChange={(e) => setLocationId(e.target.value)}
            >
              <option value="">Select a location</option>
              {locations.map((l) => (
                <option key={l.id} value={l.id}>
                  {l.name}
                </option>
              ))}
            </select>
          </label>
          <button
            type="button"
            onClick={() => locationId && load(locationId)}
            disabled={!locationId || loading}
            className="rounded border border-gray-300 px-3 py-1 text-sm font-medium text-gray-700 disabled:opacity-50"
          >
            {loading ? "Loading..." : "Refresh"}
          </button>
        </div>
      </div>

      {error && <p role="alert" className="rounded bg-red-50 p-2 text-sm text-red-700">{error}</p>}
      {!locationId && <p className="text-sm text-gray-500">Select a location to see its overview.</p>}
      {locationId && loading && !overview && <p className="text-sm text-gray-500">Loading overview...</p>}

      {overview && (
        <div className="space-y-4">
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <Card label="Assigned sensors">
              <span className="text-2xl font-semibold">{overview.device_counts.sensor}</span>
            </Card>
            <Card label="Assigned actuators">
              <span className="text-2xl font-semibold">{overview.device_counts.actuator}</span>
            </Card>
            <Card label="Strategy">
              {overview.strategy_key ? (
                <span className="font-medium">{overview.strategy_key}</span>
              ) : (
                <span className="text-gray-500">No strategy saved for this location.</span>
              )}
            </Card>
            <Card label="Last recommendation">
              {overview.last_recommendation ? (
                <div>
                  <span
                    className={`rounded px-2 py-0.5 text-xs font-medium ${
                      overview.last_recommendation.action === "irrigate"
                        ? "bg-blue-100 text-blue-800"
                        : "bg-gray-100 text-gray-700"
                    }`}
                  >
                    {overview.last_recommendation.action}
                  </span>
                  <p className="mt-1 text-xs text-gray-600">{overview.last_recommendation.reason}</p>
                </div>
              ) : (
                <span className="text-gray-500">No recommendation yet. Save a strategy first.</span>
              )}
            </Card>
          </div>

          <div className="grid gap-3 lg:grid-cols-2">
            {overview.zones.map((zone) => (
              <div key={zone.id} className="rounded border border-gray-200 p-3">
                <div className="flex items-center justify-between">
                  <h3 className="font-medium text-gray-900">{zone.name}</h3>
                  <span className="text-xs text-gray-600">
                    Moisture {zone.moisture_threshold_low} - {zone.moisture_threshold_high}
                  </span>
                </div>
                {zone.devices.length === 0 ? (
                  <p className="mt-2 text-xs text-gray-500">No devices assigned to this zone.</p>
                ) : (
                  <ul className="mt-2 space-y-2">
                    {zone.devices.map((d) => (
                      <DeviceLine
                        key={d.id}
                        device={d}
                        reading={zone.latest_readings.find((r) => r.device_id === d.id)}
                      />
                    ))}
                  </ul>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </section>
  );
}