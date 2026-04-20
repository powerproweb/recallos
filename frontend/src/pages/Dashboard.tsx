import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { apiGet } from "../api/client";

interface CheckResult { status: string; label: string; detail: string; }
interface StatusResponse { vault_path: string; overall: string; checks: CheckResult[]; counts: Record<string, number>; }
interface Job { id: number; type: string; status: string; created_at: string; }
interface OfflineStatus { offline_ready: boolean; }

const SC: Record<string, string> = { PASS: "#3fb950", WARN: "#d29922", FAIL: "#f85149", INFO: "#8b949e" };
const JC: Record<string, string> = { pending: "#d29922", running: "#58a6ff", done: "#3fb950", failed: "#f85149" };

export default function Dashboard() {
  const navigate = useNavigate();
  const [status, setStatus] = useState<StatusResponse | null>(null);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [offline, setOffline] = useState<OfflineStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");

  useEffect(() => {
    Promise.all([
      apiGet<StatusResponse>("/api/status").catch(() => null),
      apiGet<{ jobs: Job[] }>("/api/jobs?limit=5").catch(() => ({ jobs: [] })),
      apiGet<OfflineStatus>("/api/models/offline").catch(() => null),
    ]).then(([s, j, o]) => {
      if (s) setStatus(s); else setError("Could not load vault status");
      setJobs(j.jobs || []);
      setOffline(o);
      setLoading(false);
    });
  }, []);

  if (loading) return <p style={{ color: "#8b949e" }}>Loading…</p>;
  if (error && !status) return <p style={{ color: "#f85149" }}>Error: {error}</p>;

  return (
    <div>
      <h1 style={{ fontSize: "1.4rem", marginBottom: "1rem" }}>Dashboard</h1>

      {/* Global search bar */}
      <form onSubmit={(e) => { e.preventDefault(); if (query.trim()) navigate(`/search?q=${encodeURIComponent(query)}`); }}
        style={{ marginBottom: "1.25rem" }}>
        <input type="text" value={query} onChange={(e) => setQuery(e.target.value)}
          placeholder="Search your memory…" style={{
            width: "100%", padding: "0.6rem 0.85rem", background: "#0d1117",
            border: "1px solid #30363d", borderRadius: 8, color: "#c9d1d9", fontSize: "0.95rem",
          }} />
      </form>

      {/* Status cards row */}
      <div style={{ display: "flex", gap: 12, marginBottom: "1.25rem", flexWrap: "wrap" }}>
        {status && (
          <Card label="Vault" value={status.overall} color={SC[status.overall]} sub={status.vault_path} />
        )}
        {offline && (
          <Card label="Offline" value={offline.offline_ready ? "Ready" : "Not Ready"}
            color={offline.offline_ready ? "#3fb950" : "#f85149"} />
        )}
      </div>

      {/* Quick actions */}
      <div style={{ display: "flex", gap: 8, marginBottom: "1.25rem" }}>
        {[
          { label: "Upload", to: "/upload" }, { label: "Search", to: "/search" },
          { label: "Export", to: "/download" }, { label: "Doctor", to: "/support" },
        ].map((a) => (
          <button key={a.to} onClick={() => navigate(a.to)} style={{
            padding: "0.4rem 0.9rem", background: "#21262d", color: "#c9d1d9", border: "1px solid #30363d",
            borderRadius: 6, fontSize: "0.82rem", cursor: "pointer",
          }}>{a.label}</button>
        ))}
      </div>

      {/* Recent jobs */}
      {jobs.length > 0 && (
        <>
          <h2 style={{ fontSize: "1rem", marginBottom: "0.5rem" }}>Recent Jobs</h2>
          {jobs.map((j) => (
            <div key={j.id} style={{
              display: "flex", justifyContent: "space-between", background: "#0d1117",
              borderRadius: 8, padding: "0.5rem 1rem", marginBottom: 6, fontSize: "0.85rem",
            }}>
              <span><span style={{ color: "#c9d1d9" }}>#{j.id}</span> <span style={{ color: "#8b949e" }}>{j.type}</span></span>
              <span style={{ color: JC[j.status] || "#8b949e", fontWeight: 600, textTransform: "uppercase", fontSize: "0.8rem" }}>{j.status}</span>
            </div>
          ))}
        </>
      )}

      {/* Health checks */}
      {status && (
        <>
          <h2 style={{ fontSize: "1rem", marginTop: "1rem", marginBottom: "0.5rem" }}>Health Checks</h2>
          {status.checks.map((c, i) => (
            <div key={i} style={{ display: "flex", gap: 10, fontSize: "0.85rem", marginBottom: 4 }}>
              <span style={{ color: SC[c.status] || "#8b949e", fontWeight: 600, minWidth: 42 }}>{c.status}</span>
              <span>{c.label}</span>
              {c.detail && <span style={{ color: "#8b949e" }}>— {c.detail}</span>}
            </div>
          ))}
        </>
      )}
    </div>
  );
}

function Card({ label, value, color, sub }: { label: string; value: string; color?: string; sub?: string }) {
  return (
    <div style={{ background: "#0d1117", borderRadius: 8, padding: "0.8rem 1.2rem", minWidth: 140 }}>
      <div style={{ fontSize: "0.78rem", color: "#8b949e", marginBottom: 2 }}>{label}</div>
      <div style={{ fontSize: "1.1rem", fontWeight: 700, color: color || "#c9d1d9" }}>{value}</div>
      {sub && <div style={{ fontSize: "0.72rem", color: "#484f58", marginTop: 2 }}>{sub}</div>}
    </div>
  );
}
