import { useEffect, useState } from "react";
import {
  createSensor,
  getSensors,
  type SensorDto,
} from "../../services/api";

export default function SensorList() {
  const [sensors, setSensors] = useState<SensorDto[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sensorType, setSensorType] = useState("moisture");
  const [displayName, setDisplayName] = useState("");

  async function loadSensors() {
    try {
      setLoading(true);
      setError(null);
      const data = await getSensors();
      setSensors(data);
    } catch {
      setError("Unable to load sensors.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadSensors();
  }, []);

  async function handleCreate() {
    try {
      setError(null);

      const sensor = await createSensor({
        type: sensorType,
        display_name: displayName || null,
      });

      setSensors((current) => [sensor, ...current]);
      setDisplayName("");
    } catch {
      setError("Unable to create sensor.");
    }
  }

  return (
    <section className="space-y-6">
      <div>
        <h2 className="text-2xl font-semibold">Sensors</h2>
        <p className="text-gray-600">
          Manage greenhouse sensors.
        </p>
      </div>

      <div className="flex flex-wrap gap-3">
        <select
          value={sensorType}
          onChange={(event) => setSensorType(event.target.value)}
          className="rounded border px-3 py-2"
        >
          <option value="moisture">Moisture</option>
          <option value="light">Light</option>
        </select>

        <input
          value={displayName}
          onChange={(event) => setDisplayName(event.target.value)}
          placeholder="Display name"
          className="rounded border px-3 py-2"
        />

        <button
          type="button"
          onClick={handleCreate}
          className="rounded bg-black px-4 py-2 text-white"
        >
          Add sensor
        </button>
      </div>

      {loading && <p>Loading sensors...</p>}

      {error && <p className="text-red-600">{error}</p>}

      {!loading && !error && sensors.length === 0 && (
        <p className="text-gray-600">
          No sensors have been added yet.
        </p>
      )}

      {!loading && sensors.length > 0 && (
        <div className="space-y-3">
          {sensors.map((sensor) => (
            <article
              key={sensor.id}
              className="rounded border p-4"
            >
              <h3 className="font-medium">
                {sensor.display_name}
              </h3>

              <p className="text-sm text-gray-600">
                Type: {sensor.device_type}
              </p>

              <pre className="mt-2 rounded bg-gray-100 p-3 text-sm">
                {JSON.stringify(sensor.default_config, null, 2)}
              </pre>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
