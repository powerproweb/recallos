import { useEffect, useState } from "react";
import { apiGet } from "../api/client";

interface SysInfo { os: string; python: string; vault_path: string; vault_size_mb: number; recallos_version: string; }
interface DoctorReport { vault_path: string; overall: string; checks: { status: string; label: string; detail: string }[]; counts: Record<string, number>; }

const SC: Record<string, string> = { PASS: "#3fb950", WARN: "#d29922", FAIL: "#f85149", INFO: "#8b949e" };

export default function Support() {
  const [info, setInfo] = useState<SysInfo | null>(null);
  const [doctor, setDoctor] = useState<DoctorReport | null>(null);
  const [running, setRunning] = useState(false);

  useEffect(() => { apiGet<SysInfo>("/api/support/info").then(setInfo).catch(() => {}); }, []);

  const runDoctor = () => {
    setRunning(true);
    apiGet<DoctorReport>("/api/support/doctor").then(setDoctor).catch(() => {}).finally(() => setRunning(false));
  };

  return (
    <div>
      <h1 style={{ fontSize: "1.4rem", marginBottom: "1rem" }}>Support</h1>
      {info && (
        <div style={{ background: "#0d1117", borderRadius: 8, padding: "1rem 1.25rem", marginBottom: "1.25rem", fontSize: "0.85rem" }}>
          {[
            ["RecallOS", info.recallos_version], ["OS", info.os], ["Python", info.python],
            ["Vault", info.vault_path], ["Vault Size", `${info.vault_size_mb} MB`],
          ].map(([k, v]) => (
            <div key={k} style={{ marginBottom: 4 }}><span style={{ color: "#8b949e" }}>{k}: </span><span style={{ color: "#c9d1d9" }}>{v}</span></div>
          ))}
        </div>
      )}
      <button onClick={runDoctor} disabled={running} style={{
        padding: "0.45rem 1rem", background: "#238636", color: "#fff", border: "none", borderRadius: 6,
        fontSize: "0.85rem", cursor: running ? "wait" : "pointer", marginBottom: "1rem",
      }}>{running ? "Running…" : "Run Doctor"}</button>
      {doctor && (
        <div style={{ marginTop: "0.5rem" }}>
          <div style={{ fontWeight: 600, color: SC[doctor.overall] || "#c9d1d9", marginBottom: 8 }}>Overall: {doctor.overall}</div>
          {doctor.checks.map((c, i) => (
            <div key={i} style={{ fontSize: "0.85rem", marginBottom: 4, display: "flex", gap: 10 }}>
              <span style={{ color: SC[c.status] || "#8b949e", fontWeight: 600, minWidth: 42 }}>{c.status}</span>
              <span>{c.label}</span>
              {c.detail && <span style={{ color: "#8b949e" }}>— {c.detail}</span>}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
