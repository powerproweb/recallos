import { useEffect, useState } from "react";
import { apiGet } from "../api/client";

interface CheckResult {
  status: string;
  label: string;
  detail: string;
}

interface StatusResponse {
  vault_path: string;
  overall: string;
  checks: CheckResult[];
  counts: Record<string, number>;
}

const STATUS_COLORS: Record<string, string> = {
  PASS: "#3fb950",
  WARN: "#d29922",
  FAIL: "#f85149",
  INFO: "#8b949e",
};

export default function Dashboard() {
  const [status, setStatus] = useState<StatusResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiGet<StatusResponse>("/api/status")
      .then(setStatus)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p style={{ color: "#8b949e" }}>Loading vault status…</p>;
  if (error) return <p style={{ color: "#f85149" }}>Error: {error}</p>;
  if (!status) return null;

  return (
    <div>
      <h1 style={{ fontSize: "1.4rem", marginBottom: "1rem" }}>Dashboard</h1>

      <div
        style={{
          background: "#0d1117",
          borderRadius: 8,
          padding: "1rem 1.25rem",
          marginBottom: "1.25rem",
        }}
      >
        <div style={{ fontSize: "0.85rem", color: "#8b949e", marginBottom: 4 }}>
          Vault
        </div>
        <div style={{ fontSize: "1rem" }}>{status.vault_path}</div>
        <div
          style={{
            marginTop: 8,
            fontWeight: 600,
            color: STATUS_COLORS[status.overall] ?? "#c9d1d9",
          }}
        >
          Overall: {status.overall}
        </div>
      </div>

      <h2 style={{ fontSize: "1rem", marginBottom: "0.6rem" }}>Health Checks</h2>
      <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
        {status.checks.map((check, i) => (
          <div
            key={i}
            style={{
              display: "flex",
              alignItems: "baseline",
              gap: 10,
              fontSize: "0.88rem",
            }}
          >
            <span
              style={{
                color: STATUS_COLORS[check.status] ?? "#8b949e",
                fontWeight: 600,
                minWidth: 42,
              }}
            >
              {check.status}
            </span>
            <span>{check.label}</span>
            {check.detail && (
              <span style={{ color: "#8b949e", fontSize: "0.82rem" }}>
                — {check.detail}
              </span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
