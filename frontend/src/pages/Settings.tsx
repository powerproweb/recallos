import { useEffect, useState } from "react";
import { apiGet, apiPut } from "../api/client";

export default function Settings() {
  const [settings, setSettings] = useState<Record<string, string>>({});
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    apiGet<{ settings: Record<string, string> }>("/api/settings")
      .then((r) => setSettings(r.settings || {}))
      .catch(() => {});
  }, []);

  const update = (key: string, value: string) => {
    setSaved(false);
    apiPut("/api/settings", { key, value }).then(() => {
      setSettings((prev) => ({ ...prev, [key]: value }));
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    });
  };

  return (
    <div>
      <h1 style={{ fontSize: "1.4rem", marginBottom: "1rem" }}>Settings</h1>
      <div style={{ background: "#0d1117", borderRadius: 8, padding: "1rem 1.25rem" }}>
        <SettingRow label="Theme" value={settings["theme"] || "dark"}
          options={["dark", "light"]} onChange={(v) => update("theme", v)} />
        <SettingRow label="Telemetry" value={settings["network.feature.telemetry"] || "false"}
          options={["false", "true"]} onChange={(v) => update("network.feature.telemetry", v)} />
      </div>
      {saved && <p style={{ color: "#3fb950", fontSize: "0.85rem", marginTop: 8 }}>Saved.</p>}
    </div>
  );
}

function SettingRow({ label, value, options, onChange }: {
  label: string; value: string; options: string[]; onChange: (v: string) => void;
}) {
  return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 10 }}>
      <span style={{ fontSize: "0.88rem", color: "#c9d1d9" }}>{label}</span>
      <select value={value} onChange={(e) => onChange(e.target.value)} style={{
        padding: "0.35rem 0.6rem", background: "#161b22", border: "1px solid #30363d",
        borderRadius: 6, color: "#8b949e", fontSize: "0.82rem",
      }}>
        {options.map((o) => <option key={o} value={o}>{o}</option>)}
      </select>
    </div>
  );
}
