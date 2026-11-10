import { useCallback, useEffect, useState } from "react";
import { applyCommand, listActuators, listExecutions } from "./actuatorsApi";
import type { Actuator, Execution } from "./actuatorsApi";

const errMsg = (e: unknown) => (e instanceof Error ? e.message : "Something went wrong.");

export default function ExecutionLog() {
  const [actuators, setActuators] = useState<Actuator[]>([]);
  const [executions, setExecutions] = useState<Execution[]>([]);
  const [deviceId, setDeviceId] = useState("");
  const [command, setCommand] = useState("start_pump");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const [acts, execs] = await Promise.all([listActuators(), listExecutions(20)]);
      setActuators(acts);
      setExecutions(execs);
      setDeviceId((cur) => (acts.some((a) => a.id === cur) ? cur : acts[0]?.id ?? ""));
    } catch (e) {
      setError(errMsg(e));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function handleSend() {
    if (!deviceId || !command.trim()) return;
    setBusy(true);
    setError(null);
    setSuccess(null);
    try {
      await applyCommand(deviceId, command.trim());
      setSuccess("Command applied.");
    } catch (e) {
      setError(errMsg(e)); // a blocked attempt shows the policy message
    } finally {
      setBusy(false);
      await load(); // the attempt is in the log either way
    }
  }

  const nameOf = (id: string) => {
    const a = actuators.find((x) => x.id === id);
    return a ? a.display_name ?? a.device_type : id.slice(0, 8);
  };

  return (
    <section className="space-y-4 rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-900">Execution log</h2>
        <button
          type="button"
          onClick={() => void load()}
          className="rounded border border-gray-300 px-3 py-1 text-sm font-medium text-gray-700"
        >
          Refresh
        </button>
      </div>

      <p className="text-xs text-gray-600">
        Any command succeeds until the actuator has been <span className="font-medium">running</span> for 30
        minutes. A successful row has an empty message and the policy <span className="font-medium">logging</span>.
        A blocked row shows <span className="font-medium">Max run time exceeded</span> with the policies{" "}
        <span className="font-medium">maxRunTime</span> and <span className="font-medium">logging</span>.
      </p>

      <div className="flex flex-wrap items-end gap-2">
        <label className="text-xs text-gray-600">
          Actuator
          <select
            className="mt-1 block rounded border border-gray-300 px-2 py-1 text-sm"
            value={deviceId}
            onChange={(e) => setDeviceId(e.target.value)}
          >
            {actuators.length === 0 && <option value="">No actuators</option>}
            {actuators.map((a) => (
              <option key={a.id} value={a.id}>
                {a.display_name ?? a.device_type} ({a.state})
              </option>
            ))}
          </select>
        </label>
        <label className="text-xs text-gray-600">
          Command
          <input
            className="mt-1 block rounded border border-gray-300 px-2 py-1 text-sm"
            value={command}
            onChange={(e) => setCommand(e.target.value)}
          />
        </label>
        <button
          type="button"
          onClick={handleSend}
          disabled={busy || !deviceId || !command.trim()}
          className="rounded bg-green-600 px-3 py-1 text-sm font-medium text-white disabled:opacity-50"
        >
          Send command
        </button>
      </div>

      {error && <p role="alert" className="rounded bg-red-50 p-2 text-sm text-red-700">{error}</p>}
      {success && <p role="status" className="rounded bg-green-50 p-2 text-sm text-green-700">{success}</p>}
      {loading && <p className="text-sm text-gray-500">Loading executions...</p>}
      {!loading && executions.length === 0 && (
        <p className="text-sm text-gray-500">No executions yet. Send a command to create one.</p>
      )}

      {executions.length > 0 && (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-gray-200 text-xs uppercase tracking-wide text-gray-500">
                <th className="py-1 pr-3">Time</th>
                <th className="py-1 pr-3">Actuator</th>
                <th className="py-1 pr-3">Result</th>
                <th className="py-1 pr-3">Policies</th>
                <th className="py-1">Message</th>
              </tr>
            </thead>
            <tbody>
              {executions.map((x) => (
                <tr key={x.id} className="border-b border-gray-100 align-top">
                  <td className="py-1 pr-3 text-xs text-gray-600">{new Date(x.created_at).toLocaleString()}</td>
                  <td className="py-1 pr-3">{nameOf(x.device_id)}</td>
                  <td className="py-1 pr-3">
                    <span
                      className={`rounded px-2 py-0.5 text-xs font-medium ${
                        x.success ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"
                      }`}
                    >
                      {x.success ? "success" : "blocked"}
                    </span>
                  </td>
                  <td className="py-1 pr-3">
                    <div className="flex flex-wrap gap-1">
                      {x.policy_applied.map((p) => (
                        <span key={p} className="rounded bg-gray-100 px-2 py-0.5 text-xs text-gray-700">
                          {p}
                        </span>
                      ))}
                    </div>
                  </td>
                  <td className="py-1 text-xs text-gray-700">{x.message ?? "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}