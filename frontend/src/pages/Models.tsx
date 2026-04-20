import { useEffect, useState } from "react";
import { apiGet, apiPost } from "../api/client";

interface ModelInfo {
  name: string;
  installed: boolean;
  cache_dir: string;
  model_dir: string;
  expected_sha256: string;
  size_bytes: number;
  verified: boolean;
  download_url?: string;
}

interface OfflineStatus {
  offline_ready: boolean;
  checks: Record<string, { ok: boolean; detail: string }>;
}

export default function Models() {
  const [model, setModel] = useState<ModelInfo | null>(null);
  const [offline, setOffline] = useState<OfflineStatus | null>(null);
  const [downloading, setDownloading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const load = () => {
    apiGet<ModelInfo>("/api/models").then(setModel).catch(() => {});
    apiGet<OfflineStatus>("/api/models/offline").then(setOffline).catch(() => {});
  };

  useEffect(load, []);

  const handleDownload = () => {
    setDownloading(true);
    setMessage(null);
    apiPost<{ status: string; message: string }>("/api/models/download", {})
      .then((r) => { setMessage(r.message); load(); })
      .catch((e) => setMessage(`Error: ${e.message}`))
      .finally(() => setDownloading(false));
  };

  if (!model) return <p style={{ color: "#8b949e" }}>Loading…</p>;

  return (
    <div>
      <h1 style={{ fontSize: "1.4rem", marginBottom: "1rem" }}>Model Manager</h1>

      {/* Offline status badge */}
      {offline && (
        <div style={{
          display: "inline-block", padding: "0.35rem 0.8rem", borderRadius: 6, marginBottom: "1rem",
          background: offline.offline_ready ? "#0d1117" : "#2d1b1b",
          border: `1px solid ${offline.offline_ready ? "#238636" : "#f85149"}`,
          fontSize: "0.82rem", fontWeight: 600,
          color: offline.offline_ready ? "#3fb950" : "#f85149",
        }}>
          {offline.offline_ready ? "Offline Ready" : "Not Offline Ready"}
        </div>
      )}

      {/* Model info */}
      <div style={{ background: "#0d1117", borderRadius: 8, padding: "1rem 1.25rem", marginBottom: "1rem" }}>
        <div style={{ marginBottom: 8 }}>
          <span style={{ fontSize: "0.85rem", color: "#8b949e" }}>Model: </span>
          <span style={{ fontSize: "0.95rem", color: "#c9d1d9", fontWeight: 600 }}>{model.name}</span>
        </div>
        <div style={{ fontSize: "0.82rem", color: "#8b949e", marginBottom: 4 }}>
          Status: <span style={{ color: model.installed ? "#3fb950" : "#f85149" }}>
            {model.installed ? "Installed" : "Not installed"}
          </span>
          {model.verified && <span style={{ color: "#3fb950" }}> · Verified</span>}
        </div>
        {model.installed && (
          <div style={{ fontSize: "0.78rem", color: "#484f58" }}>
            Size: {(model.size_bytes / (1024 * 1024)).toFixed(1)} MB · {model.model_dir}
          </div>
        )}
        {!model.installed && (
          <button onClick={handleDownload} disabled={downloading} style={{
            marginTop: 10, padding: "0.45rem 1rem", background: "#238636", color: "#fff",
            border: "none", borderRadius: 6, fontSize: "0.85rem", cursor: downloading ? "wait" : "pointer",
          }}>
            {downloading ? "Downloading..." : "Download Model"}
          </button>
        )}
      </div>

      {message && <p style={{ color: message.startsWith("Error") ? "#f85149" : "#3fb950", fontSize: "0.85rem" }}>{message}</p>}

      {/* SHA-256 */}
      <div style={{ fontSize: "0.75rem", color: "#484f58", wordBreak: "break-all" }}>
        SHA-256: {model.expected_sha256}
      </div>
    </div>
  );
}
