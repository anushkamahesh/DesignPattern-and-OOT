import { useEffect, useRef, useState } from "react";
import { getReadings, readSensor, updateSampling, type Reading } from "./readingsApi";

const SOURCE_STYLES: Record<string, string> = {
  simulation: "bg-blue-100 text-blue-800",
  vendor: "bg-purple-100 text-purple-800",
  mqtt: "bg-orange-100 text-orange-800",
};

// Temporary poll until Phase 12 replaces this with a WebSocket push.
const POLL_MS = 5000;

export default function SensorReadingPanel({ deviceId }: { deviceId: string }) {
  const [latest, setLatest] = useState<Reading | null>(null);
  const [intervalInput, setIntervalInput] = useState("300");
  const [tracking, setTracking] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const mounted = useRef(true);

  async function refresh() {
    try {
      const rows = await getReadings(deviceId, 1);
      if (mounted.current && rows.length > 0) setLatest(rows[0]);
    } catch {
      /* ignore transient poll failures, keep the last known value on screen */
    }
  }

  useEffect(() => {
    mounted.current = true;
    refresh();
    const id = window.setInterval(refresh, POLL_MS); // temporary poll, see note above
    return () => {
      mounted.current = false;
      window.clearInterval(id);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [deviceId]);

  async function handleRead() {
    setBusy(true);
    setError(null);
    try {
      const r = await readSensor(deviceId);
      setLatest(r);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Read failed.");
    } finally {
      setBusy(false);
    }
  }

  async function handleSave() {
    setBusy(true);
    setError(null);
    const seconds = Number(intervalInput);
    if (!Number.isFinite(seconds) || seconds < 5) {
      setError("Interval must be at least 5 seconds.");
      setBusy(false);
      return;
    }
    try {
      await updateSampling(deviceId, {
        sampling_interval_seconds: seconds,
        tracking_enabled: tracking,
      });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not update sampling.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mt-3 space-y-2 border-t pt-3 text-sm">
      <div className="flex flex-wrap items-center gap-2">
        <button
          type="button"
          onClick={handleRead}
          disabled={busy}
          className="rounded bg-emerald-600 px-3 py-1 text-white disabled:opacity-50"
        >
          Read now
        </button>
        {latest ? (
          <>
            <span className="font-medium">
              {latest.value} {latest.unit}
            </span>
            <span
              className={`rounded px-2 py-0.5 text-xs ${
                SOURCE_STYLES[latest.source] ?? "bg-gray-100 text-gray-700"
              }`}
            >
              {latest.source}
            </span>
          </>
        ) : (
          <span className="text-xs text-gray-500">No reading yet.</span>
        )}
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <label className="text-xs text-gray-600">
          Interval (s)
          <input
            className="ml-1 w-20 rounded border px-2 py-1"
            value={intervalInput}
            onChange={(e) => setIntervalInput(e.target.value)}
          />
        </label>
        <label className="flex items-center gap-1 text-xs text-gray-600">
          <input
            type="checkbox"
            checked={tracking}
            onChange={(e) => setTracking(e.target.checked)}
          />
          Tracking on
        </label>
        <button
          type="button"
          onClick={handleSave}
          disabled={busy}
          className="rounded border px-2 py-1 text-xs"
        >
          Save
        </button>
      </div>

      {error && (
        <p role="alert" className="text-xs text-red-700">
          {error}
        </p>
      )}
    </div>
  );
}