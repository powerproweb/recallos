import { useEffect, useState } from "react";
import { apiGet } from "../api/client";

interface MCPStatus {
  available: boolean;
  tool_count: number;
  setup_command: string;
  tools: { name: string; description: string }[];
}

export default function MCP() {
  const [status, setStatus] = useState<MCPStatus | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => { apiGet<MCPStatus>("/api/mcp/status").then(setStatus).catch(() => {}); }, []);

  const copy = () => {
    if (status) {
      navigator.clipboard.writeText(status.setup_command).then(() => { setCopied(true); setTimeout(() => setCopied(false), 2000); });
    }
  };

  if (!status) return <p style={{ color: "#8b949e" }}>Loading…</p>;

  return (
    <div>
      <h1 style={{ fontSize: "1.4rem", marginBottom: "1rem" }}>MCP Setup</h1>

      <div style={{ background: "#0d1117", borderRadius: 8, padding: "1rem 1.25rem", marginBottom: "1.25rem" }}>
        <div style={{ fontSize: "0.85rem", color: "#8b949e", marginBottom: 6 }}>
          Status: <span style={{ color: status.available ? "#3fb950" : "#f85149", fontWeight: 600 }}>
            {status.available ? `Available (${status.tool_count} tools)` : "Not available"}
          </span>
        </div>
        <div style={{ fontSize: "0.82rem", color: "#8b949e", marginBottom: 8 }}>Setup command:</div>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <code style={{
            flex: 1, background: "#161b22", padding: "0.5rem 0.75rem", borderRadius: 6,
            fontSize: "0.8rem", color: "#c9d1d9", wordBreak: "break-all", border: "1px solid #30363d",
          }}>{status.setup_command}</code>
          <button onClick={copy} style={{
            padding: "0.4rem 0.8rem", background: copied ? "#238636" : "#30363d", color: "#fff",
            border: "none", borderRadius: 6, fontSize: "0.8rem", cursor: "pointer", whiteSpace: "nowrap",
          }}>{copied ? "Copied!" : "Copy"}</button>
        </div>
      </div>

      {status.tools.length > 0 && (
        <>
          <h2 style={{ fontSize: "1rem", marginBottom: "0.5rem" }}>Available Tools ({status.tool_count})</h2>
          {status.tools.map((t) => (
            <div key={t.name} style={{ fontSize: "0.85rem", marginBottom: 6 }}>
              <span style={{ color: "#58a6ff", fontWeight: 600 }}>{t.name}</span>
              <span style={{ color: "#8b949e" }}> — {t.description.slice(0, 100)}</span>
            </div>
          ))}
        </>
      )}
    </div>
  );
}
