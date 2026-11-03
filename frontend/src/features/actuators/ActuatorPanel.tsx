import { useCallback, useEffect, useState } from "react";
import { listActuators, transitionActuator } from "./actuatorsApi";
import type { Actuator } from "./actuatorsApi";

// Display only: the names of the states. Which moves are legal comes from the API
// (allowed_targets / allowed_commands); the rules live in the backend domain.
const STATES = ["off", "idle", "running", "error", "maintenance"];

const BADGE: Record<string, string> = {
  off: "bg-gray-200 text-gray-800",
  idle: "bg-green-100 text-green-800",
  running: "bg-blue-100 text-blue-800",
  error: "bg-red-100 text-red-800",
  maintenance: "bg-amber-100 text-amber-800",
};

const errMsg = (e: unknown) => (e instanceof Error ? e.message : "Something went wrong.");

export default function ActuatorPanel() {
  const [actuators, setActuators] = useState<Actuator[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setActuators(await listActuators());
      setError(null);
    } catch (e) {
      setError(errMsg(e));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function handleTransition(actuator: Actuator, target: string) {
    setBusyId(actuator.id);
    setError(null);
    setSuccess(null);
    try {
      const updated = await transitionActuator(actuator.id, target);
      setActuators((current) => current.map((a) => (a.id === updated.id ? updated : a)));
      setSuccess(`${updated.display_name ?? updated.device_type} is now ${updated.state}.`);
    } catch (e) {
      setError(errMsg(e)); // e.g. the 409 explanation from the server
      void load();
    } finally {
      setBusyId(null);
    }
  }

  return (
    <section className="space-y-4 rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-900">Actuators</h2>
        <button
          type="button"
          onClick={() => void load()}
          className="rounded border border-gray-300 px-3 py-1 text-sm font-medium text-gray-700"
        >
          Refresh
        </button>
      </div>

      {error && <p role="alert" className="rounded bg-red-50 p-2 text-sm text-red-700">{error}</p>}
      {success && <p role="status" className="rounded bg-green-50 p-2 text-sm text-green-700">{success}</p>}
      {loading && <p className="text-sm text-gray-500">Loading actuators...</p>}
      {!loading && actuators.length === 0 && (
        <p className="text-sm text-gray-500">No actuators yet.</p>
      )}

      <ul className="space-y-3">
        {actuators.map((a) => (
          <li key={a.id} className="rounded border border-gray-200 p-3">
            <div className="flex items-center justify-between gap-2">
              <div>
                <p className="font-medium text-gray-900">{a.display_name ?? a.device_type}</p>
                <p className="text-xs text-gray-500">
                  {a.device_type} &middot; {a.device_family}
                </p>
              </div>
              <span className={`rounded px-2 py-0.5 text-xs font-medium ${BADGE[a.state] ?? "bg-gray-100 text-gray-700"}`}>
                {a.state}
              </span>
            </div>

            <div className="mt-2 flex flex-wrap gap-2">
              {STATES.map((target) => {
                const legal = a.allowed_targets.includes(target);
                const isCurrent = target === a.state;
                const reason = isCurrent
                  ? `Already ${a.state}.`
                  : `Not allowed from ${a.state}. Allowed: ${a.allowed_targets.join(", ") || "none"}.`;
                return (
                  <button
                    key={target}
                    type="button"
                    disabled={!legal || busyId === a.id}
                    title={legal ? `Move to ${target}` : reason}
                    onClick={() => handleTransition(a, target)}
                    className="rounded border border-gray-300 px-2 py-1 text-xs font-medium text-gray-700 disabled:cursor-not-allowed disabled:opacity-40"
                  >
                    {target}
                  </button>
                );
              })}
            </div>

            <p className="mt-2 text-xs text-gray-500">
              Allowed commands: {a.allowed_commands.join(", ") || "none"}
            </p>
          </li>
        ))}
      </ul>
    </section>
  );
}