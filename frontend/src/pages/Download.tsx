import { useState } from "react";
import { apiGet } from "../api/client";

export default function Download() {
  const [loading, setLoading] = useState<string | null>(null);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const exportData = (format: string) => {
    setLoading(format);
    setError(null);
    const url = format === "recallscript" ? "/api/export/recallscript" : "/api/export/vault";
    apiGet<any>(url)
      .then((data) => {
        if (data.error) { setError(data.error); setResult(null); }
        else {
          setResult(data);
          // Trigger browser download
          const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
          const a = document.createElement("a");
          a.href = URL.createObjectURL(blob);
          a.download = `recallos-export-${format}.json`;
          a.click();
        }
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(null));
  };

  return (
    <div>
      <h1 style={{ fontSize: "1.4rem", marginBottom: "1rem" }}>Export</h1>
      <div style={{ display: "flex", gap: 10, marginBottom: "1rem" }}>
        {["vault", "recallscript"].map((fmt) => (
          <button key={fmt} onClick={() => exportData(fmt)} disabled={loading !== null} style={{
            padding: "0.5rem 1.1rem", background: "#238636", color: "#fff", border: "none",
            borderRadius: 6, fontSize: "0.88rem", cursor: loading ? "wait" : "pointer",
            textTransform: "capitalize",
          }}>
            {loading === fmt ? "Exporting..." : `Export ${fmt}`}
          </button>
        ))}
      </div>
      {error && <p style={{ color: "#f85149", fontSize: "0.88rem" }}>Error: {error}</p>}
      {result && <p style={{ color: "#3fb950", fontSize: "0.88rem" }}>Exported {result.count} records.</p>}
    </div>
  );
}
