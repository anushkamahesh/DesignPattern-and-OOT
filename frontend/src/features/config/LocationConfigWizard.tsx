import { useCallback, useEffect, useState } from "react";
import {
  addZone,
  createLocationConfig,
  deleteLocation,
  deleteZone,
  getLocationConfig,
  listLocations,
  listZoneDevices,
  updateZone,
} from "./locationsApi";
import type { LocationConfig, LocationSummary, ZoneDevice, ZoneInput } from "./locationsApi";
import { emptyZoneForm, parseZoneForm, zoneToForm } from "./zoneForm";
import type { ZoneForm } from "./zoneForm";

const errMsg = (e: unknown) => (e instanceof Error ? e.message : "Something went wrong.");

const inputCls =
  "w-full rounded border border-gray-300 px-2 py-1 text-sm focus:border-green-600 focus:outline-none";
const btnCls = "rounded px-3 py-1 text-sm font-medium disabled:opacity-50";
const primaryBtn = `${btnCls} bg-green-600 text-white hover:bg-green-700`;
const secondaryBtn = `${btnCls} border border-gray-300 text-gray-700 hover:bg-gray-100`;
const dangerBtn = `${btnCls} border border-red-300 text-red-700 hover:bg-red-50`;

function ZoneFields({ value, onChange }: { value: ZoneForm; onChange: (v: ZoneForm) => void }) {
  const set = (patch: Partial<ZoneForm>) => onChange({ ...value, ...patch });
  return (
    <div className="grid grid-cols-1 gap-2 sm:grid-cols-4">
      <label className="text-xs text-gray-600 sm:col-span-2">
        Zone name
        <input className={inputCls} value={value.name} onChange={(e) => set({ name: e.target.value })} />
      </label>
      <label className="text-xs text-gray-600">
        Low (0-1)
        <input className={inputCls} value={value.low} inputMode="decimal" onChange={(e) => set({ low: e.target.value })} />
      </label>
      <label className="text-xs text-gray-600">
        High (0-1)
        <input className={inputCls} value={value.high} inputMode="decimal" onChange={(e) => set({ high: e.target.value })} />
      </label>
      <label className="text-xs text-gray-600 sm:col-span-4">
        Schedule (JSON object, optional)
        <input
          className={inputCls}
          value={value.schedule}
          placeholder='{"start":"06:00","end":"18:00"}'
          onChange={(e) => set({ schedule: e.target.value })}
        />
      </label>
    </div>
  );
}

export default function LocationConfigWizard({ onChanged }: { onChanged?: () => void }) {
  const [locations, setLocations] = useState<LocationSummary[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [config, setConfig] = useState<LocationConfig | null>(null);
  const [zoneDevices, setZoneDevices] = useState<Record<string, ZoneDevice[]>>({});
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const [newName, setNewName] = useState("");
  const [newZones, setNewZones] = useState<ZoneForm[]>([emptyZoneForm()]);
  const [createError, setCreateError] = useState<string | null>(null);

  const [addForm, setAddForm] = useState<ZoneForm>(emptyZoneForm());
  const [addError, setAddError] = useState<string | null>(null);

  const [editingId, setEditingId] = useState<string | null>(null);
  const [editForm, setEditForm] = useState<ZoneForm>(emptyZoneForm());
  const [editError, setEditError] = useState<string | null>(null);

  const refreshLocations = useCallback(async () => {
    setLocations(await listLocations());
  }, []);

  const loadConfig = useCallback(async (id: string) => {
    const cfg = await getLocationConfig(id);
    const lists = await Promise.all(cfg.zones.map((z) => listZoneDevices(id, z.id)));
    const map: Record<string, ZoneDevice[]> = {};
    cfg.zones.forEach((z, i) => {
      map[z.id] = lists[i];
    });
    setConfig(cfg);
    setZoneDevices(map);
  }, []);

  useEffect(() => {
    refreshLocations().catch((e) => setError(errMsg(e)));
  }, [refreshLocations]);

  function clearMessages() {
    setError(null);
    setSuccess(null);
  }

  async function handleSelect(id: string) {
    clearMessages();
    setEditingId(null);
    setSelectedId(id);
    try {
      await loadConfig(id);
    } catch (e) {
      setError(errMsg(e));
    }
  }

  async function handleCreate() {
    clearMessages();
    setCreateError(null);
    if (!newName.trim()) {
      setCreateError("Location name is required.");
      return;
    }
    const zones: ZoneInput[] = [];
    const seen = new Set<string>();
    for (let i = 0; i < newZones.length; i++) {
      const r = parseZoneForm(newZones[i]);
      if (!r.value) {
        setCreateError(`Zone ${i + 1}: ${r.error}`);
        return;
      }
      const key = r.value.name.toLowerCase();
      if (seen.has(key)) {
        setCreateError(`Zone names must be unique ("${r.value.name}" is repeated).`);
        return;
      }
      seen.add(key);
      zones.push(r.value);
    }
    try {
      const created = await createLocationConfig(newName.trim(), zones);
      await refreshLocations();
      setSelectedId(created.location.id);
      await loadConfig(created.location.id);
      setNewName("");
      setNewZones([emptyZoneForm()]);
      setSuccess(`Location "${created.location.name}" created.`);
      onChanged?.();
    } catch (e) {
      setCreateError(errMsg(e));
    }
  }

  async function handleDeleteLocation(loc: LocationSummary) {
    if (!window.confirm(`Delete location "${loc.name}" and all its zones? Devices are kept but unassigned.`)) {
      return;
    }
    clearMessages();
    try {
      await deleteLocation(loc.id);
      if (selectedId === loc.id) {
        setSelectedId(null);
        setConfig(null);
        setZoneDevices({});
        setEditingId(null);
      }
      await refreshLocations();
      setSuccess(`Location "${loc.name}" deleted.`);
      onChanged?.();
    } catch (e) {
      setError(errMsg(e));
    }
  }

  async function handleAddZone() {
    if (!selectedId) return;
    clearMessages();
    setAddError(null);
    const r = parseZoneForm(addForm);
    if (!r.value) {
      setAddError(r.error ?? "Invalid zone.");
      return;
    }
    try {
      await addZone(selectedId, r.value);
      await loadConfig(selectedId);
      setAddForm(emptyZoneForm());
      setSuccess(`Zone "${r.value.name}" added.`);
      onChanged?.();
    } catch (e) {
      setAddError(errMsg(e));
    }
  }

  async function handleSaveEdit(zoneId: string) {
    if (!selectedId) return;
    clearMessages();
    setEditError(null);
    const r = parseZoneForm(editForm);
    if (!r.value) {
      setEditError(r.error ?? "Invalid zone.");
      return;
    }
    try {
      await updateZone(selectedId, zoneId, r.value);
      await loadConfig(selectedId);
      setEditingId(null);
      setSuccess("Zone updated.");
      onChanged?.();
    } catch (e) {
      setEditError(errMsg(e));
    }
  }

  async function handleDeleteZone(zoneId: string, zoneName: string) {
    if (!selectedId) return;
    if (!window.confirm(`Delete zone "${zoneName}"? Its devices will become unassigned.`)) return;
    clearMessages();
    try {
      await deleteZone(selectedId, zoneId);
      await loadConfig(selectedId);
      setSuccess(`Zone "${zoneName}" deleted.`);
      onChanged?.();
    } catch (e) {
      setError(errMsg(e));
    }
  }

  return (
    <section className="space-y-6 rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
      <h2 className="text-lg font-semibold text-gray-900">Location configuration</h2>

      {error && <p role="alert" className="rounded bg-red-50 p-2 text-sm text-red-700">{error}</p>}
      {success && <p role="status" className="rounded bg-green-50 p-2 text-sm text-green-700">{success}</p>}

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Saved locations */}
        <div>
          <h3 className="mb-2 text-sm font-semibold text-gray-700">Saved locations (newest first)</h3>
          {locations.length === 0 ? (
            <p className="text-sm text-gray-500">No locations yet. Create one to get started.</p>
          ) : (
            <ul className="space-y-1">
              {locations.map((loc) => (
                <li
                  key={loc.id}
                  className={`flex items-center justify-between rounded border px-3 py-2 text-sm ${
                    loc.id === selectedId ? "border-green-600 bg-green-50" : "border-gray-200"
                  }`}
                >
                  <button className="flex-1 text-left font-medium" onClick={() => handleSelect(loc.id)}>
                    {loc.name}
                  </button>
                  <button className={dangerBtn} onClick={() => handleDeleteLocation(loc)}>
                    Delete
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Create wizard */}
        <div>
          <h3 className="mb-2 text-sm font-semibold text-gray-700">New location</h3>
          <label className="mb-2 block text-xs text-gray-600">
            Location name
            <input className={inputCls} value={newName} onChange={(e) => setNewName(e.target.value)} />
          </label>
          <div className="space-y-3">
            {newZones.map((z, i) => (
              <div key={i} className="rounded border border-gray-200 p-2">
                <ZoneFields
                  value={z}
                  onChange={(v) => setNewZones(newZones.map((old, j) => (j === i ? v : old)))}
                />
                {newZones.length > 1 && (
                  <button
                    className="mt-1 text-xs text-red-700 underline"
                    onClick={() => setNewZones(newZones.filter((_, j) => j !== i))}
                  >
                    Remove zone {i + 1}
                  </button>
                )}
              </div>
            ))}
          </div>
          <div className="mt-2 flex gap-2">
            <button className={secondaryBtn} onClick={() => setNewZones([...newZones, emptyZoneForm()])}>
              Add another zone
            </button>
            <button className={primaryBtn} onClick={handleCreate}>
              Create location
            </button>
          </div>
          {createError && <p role="alert" className="mt-2 text-sm text-red-700">{createError}</p>}
        </div>
      </div>

      {/* Selected location */}
      {config && selectedId && (
        <div className="space-y-3 border-t border-gray-200 pt-4">
          <div>
            <h3 className="text-base font-semibold text-gray-900">{config.location.name}</h3>
            <p className="text-xs text-gray-500">Location id: {config.location.id}</p>
          </div>

          <ul className="space-y-2">
            {config.zones.map((z) => (
              <li key={z.id} className="rounded border border-gray-200 p-3 text-sm">
                {editingId === z.id ? (
                  <div className="space-y-2">
                    <ZoneFields value={editForm} onChange={setEditForm} />
                    {editError && <p role="alert" className="text-sm text-red-700">{editError}</p>}
                    <div className="flex gap-2">
                      <button className={primaryBtn} onClick={() => handleSaveEdit(z.id)}>Save</button>
                      <button className={secondaryBtn} onClick={() => setEditingId(null)}>Cancel</button>
                    </div>
                  </div>
                ) : (
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="font-medium">{z.name}</p>
                      <p className="text-xs text-gray-600">
                        Moisture {z.moisture_threshold_low} - {z.moisture_threshold_high}
                        {Object.keys(z.schedule ?? {}).length > 0 && ` | Schedule ${JSON.stringify(z.schedule)}`}
                      </p>
                      <p className="mt-1 text-xs text-gray-600">
                        Devices:{" "}
                        {(zoneDevices[z.id] ?? []).length === 0
                          ? "none assigned"
                          : (zoneDevices[z.id] ?? []).map((d) => d.display_name ?? d.device_type).join(", ")}
                      </p>
                    </div>
                    <div className="flex gap-2">
                      <button
                        className={secondaryBtn}
                        onClick={() => {
                          setEditingId(z.id);
                          setEditForm(zoneToForm(z));
                          setEditError(null);
                        }}
                      >
                        Edit
                      </button>
                      <button className={dangerBtn} onClick={() => handleDeleteZone(z.id, z.name)}>
                        Delete
                      </button>
                    </div>
                  </div>
                )}
              </li>
            ))}
          </ul>

          <div className="rounded border border-dashed border-gray-300 p-3">
            <h4 className="mb-2 text-sm font-semibold text-gray-700">Add a zone to this location</h4>
            <ZoneFields value={addForm} onChange={setAddForm} />
            {addError && <p role="alert" className="mt-2 text-sm text-red-700">{addError}</p>}
            <button className={`${primaryBtn} mt-2`} onClick={handleAddZone}>Add zone</button>
          </div>
        </div>
      )}
    </section>
  );
}