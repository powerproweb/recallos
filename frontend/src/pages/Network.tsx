import { useEffect, useState } from "react";
import { apiGet, apiPut } from "../api/client";

interface PolicyState {
  enabled: boolean;
  features: Record<string, boolean>;
}

interface LogEntry {
  feature: string;
  host: string;
  path: string;
  allowed: boolean;
  timestamp: string;
}

export default function Network() {
  const [policy, setPolicy] = useState<PolicyState | null>(null);
  const [log, setLog] = useState<LogEntry[]>([]);

  const load = () => {
    apiGet<PolicyState>("/api/network/policy").then(setPolicy).catch(() => {});
    apiGet<{ entries: LogEntry[] }>("/api/network/log?limit=50").then((r) => setLog(r.entries || [])).catch(() => {});
  };

  useEffect(load, []);

  const toggle = (key: string, current: boolean) => {
    if (key === "enabled") {
      apiPut("/api/network/policy", { enabled: !current }).then(load);
    } else {
      apiPut("/api/network/policy", { features: { [key]: !current } }).then(load);
    }
  };

  if (!policy) return <p style={{ color: "#8b949e" }}>Loading…</p>;

  return (
    <div>
      <h1 style={{ fontSize: "1.4rem", marginBottom: "1rem" }}>Network & Privacy</h1>

      <div style={{ background: "#0d1117", borderRadius: 8, padding: "1rem 1.25rem", marginBottom: "1.25rem" }}>
        <Toggle label="Global Network Access" on={policy.enabled} onToggle={() => toggle("enabled", policy.enabled)} />
        <div style={{ marginTop: 12, paddingLeft: 8, opacity: policy.enabled ? 1 : 0.4 }}>
          {Object.entries(policy.features).map(([feat, on]) => (
            <Toggle key={feat} label={feat} on={on} onToggle={() => toggle(feat, on)} />
          ))}
        </div>
      </div>

      <h2 style={{ fontSize: "1rem", marginBottom: "0.5rem" }}>Activity Log</h2>
      {log.length === 0 ? (
        <p style={{ color: "#8b949e", fontSize: "0.88rem" }}>No network activity logged yet.</p>
      ) : (
        log.map((e, i) => (
          <div key={i} style={{ fontSize: "0.82rem", marginBottom: 4, display: "flex", gap: 10 }}>
            <span style={{ color: e.allowed ? "#3fb950" : "#f85149", fontWeight: 600, minWidth: 50 }}>
              {e.allowed ? "ALLOW" : "DENY"}
            </span>
            <span style={{ color: "#8b949e" }}>{e.feature}</span>
            <span style={{ color: "#c9d1d9" }}>{e.host}{e.path}</span>
            <span style={{ color: "#484f58", marginLeft: "auto" }}>{e.timestamp}</span>
          </div>
        ))
      )}
    </div>
  );
}

function Toggle({ label, on, onToggle }: { label: string; on: boolean; onToggle: () => void }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 6, cursor: "pointer" }} onClick={onToggle}>
      <div style={{
        width: 36, height: 20, borderRadius: 10, background: on ? "#238636" : "#30363d",
        position: "relative", transition: "background 0.15s",
      }}>
        <div style={{
          width: 16, height: 16, borderRadius: 8, background: "#fff",
          position: "absolute", top: 2, left: on ? 18 : 2, transition: "left 0.15s",
        }} />
      </div>
      <span style={{ fontSize: "0.88rem", color: "#c9d1d9", textTransform: "capitalize" }}>{label}</span>
    </div>
  );
}
