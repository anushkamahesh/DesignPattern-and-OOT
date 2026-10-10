import { useEffect, useState } from "react";
import { listLocations } from "../config/locationsApi";
import type { LocationSummary } from "../config/locationsApi";
import { evaluateLocation, getRule, listStrategies, saveRule } from "./automationApi";
import type { Evaluation } from "./automationApi";

const errMsg = (e: unknown) => (e instanceof Error ? e.message : "Something went wrong.");

export default function StrategyPanel({ refreshKey = 0 }: { refreshKey?: number }) {
  const [locations, setLocations] = useState<LocationSummary[]>([]);
  const [strategies, setStrategies] = useState<string[]>([]);
  const [locationId, setLocationId] = useState("");
  const [savedKey, setSavedKey] = useState<string | null>(null);
  const [selectedKey, setSelectedKey] = useState("");
  const [result, setResult] = useState<Evaluation | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    listStrategies().then(setStrategies).catch((e) => setError(errMsg(e)));
  }, []);

  useEffect(() => {
    listLocations()
      .then((locs) => {
        setLocations(locs);
        // drop the selection if that location was deleted in the wizard
        setLocationId((current) => (locs.some((l) => l.id === current) ? current : ""));
      })
      .catch((e) => setError(errMsg(e)));
  }, [refreshKey]);

  useEffect(() => {
    setResult(null);
    setSuccess(null);
    setError(null);
    if (!locationId) {
      setSavedKey(null);
      setSelectedKey("");
      return;
    }
    getRule(locationId)
      .then((rule) => {
        setSavedKey(rule.strategy_key);
        setSelectedKey(rule.strategy_key ?? "");
      })
      .catch((e) => setError(errMsg(e)));
  }, [locationId]);

  async function handleSave() {
    if (!locationId || !selectedKey) return;
    setBusy(true);
    setError(null);
    setSuccess(null);
    try {
      const rule = await saveRule(locationId, selectedKey);
      setSavedKey(rule.strategy_key);
      setSuccess(`Strategy "${rule.strategy_key}" saved.`);
    } catch (e) {
      setError(errMsg(e));
    } finally {
      setBusy(false);
    }
  }

  async function handleEvaluate() {
    if (!locationId) return;
    setBusy(true);
    setError(null);
    setSuccess(null);
    try {
      setResult(await evaluateLocation(locationId));
    } catch (e) {
      setResult(null);
      setError(errMsg(e));
    } finally {
      setBusy(false);
    }
  }

  const unsaved = selectedKey !== "" && selectedKey !== savedKey;

  return (
    <section className="space-y-4 rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
      <h2 className="text-lg font-semibold text-gray-900">Automation strategy</h2>

      <div className="flex flex-wrap items-end gap-3">
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

        <label className="text-xs text-gray-600">
          Strategy
          <select
            className="mt-1 block rounded border border-gray-300 px-2 py-1 text-sm"
            value={selectedKey}
            disabled={!locationId}
            onChange={(e) => setSelectedKey(e.target.value)}
          >
            <option value="">Select a strategy</option>
            {strategies.map((k) => (
              <option key={k} value={k}>
                {k}
              </option>
            ))}
          </select>
        </label>

        <button
          type="button"
          onClick={handleSave}
          disabled={busy || !locationId || !selectedKey}
          className="rounded bg-green-600 px-3 py-1 text-sm font-medium text-white disabled:opacity-50"
        >
          Save strategy
        </button>
        <button
          type="button"
          onClick={handleEvaluate}
          disabled={busy || !locationId || !savedKey}
          className="rounded border border-gray-300 px-3 py-1 text-sm font-medium text-gray-700 disabled:opacity-50"
        >
          Evaluate
        </button>
      </div>

      {unsaved && (
        <p className="text-xs text-amber-700">
          Unsaved change: Evaluate uses the saved strategy ({savedKey ?? "none yet"}), so save first.
        </p>
      )}
      {error && <p role="alert" className="rounded bg-red-50 p-2 text-sm text-red-700">{error}</p>}
      {success && <p role="status" className="rounded bg-green-50 p-2 text-sm text-green-700">{success}</p>}

      {result && (
        <div>
          <p className="mb-2 text-xs text-gray-500">
            Evaluated with <span className="font-medium">{result.strategy_key}</span>
          </p>
          <ul className="space-y-2">
            {result.recommendations.map((r) => (
              <li key={r.zone_id} className="rounded border border-gray-200 p-3 text-sm">
                <div className="flex items-center justify-between">
                  <span className="font-medium">{r.zone_name}</span>
                  <span
                    className={`rounded px-2 py-0.5 text-xs font-medium ${
                      r.action === "irrigate" ? "bg-blue-100 text-blue-800" : "bg-gray-100 text-gray-700"
                    }`}
                  >
                    {r.action}
                  </span>
                </div>
                <p className="mt-1 text-xs text-gray-600">{r.reason}</p>
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}