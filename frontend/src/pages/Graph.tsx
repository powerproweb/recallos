import { useEffect, useState } from "react";
import { apiGet } from "../api/client";

interface VaultStats {
  total_nodes: number;
  link_nodes: number;
  total_edges: number;
  nodes_per_domain: Record<string, number>;
  top_links: { node: string; domains: string[]; count: number }[];
}

interface Triple {
  subject: string;
  predicate: string;
  object: string;
  valid_from: string | null;
  valid_to: string | null;
}

export default function Graph() {
  const [vault, setVault] = useState<VaultStats | null>(null);
  const [triples, setTriples] = useState<Triple[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      apiGet<VaultStats>("/api/graph/vault").catch(() => null),
      apiGet<{ triples: Triple[] }>("/api/graph/recall/triples?limit=50").catch(() => ({ triples: [] })),
    ]).then(([v, t]) => {
      setVault(v);
      setTriples(t.triples || []);
      setLoading(false);
    });
  }, []);

  if (loading) return <p style={{ color: "#8b949e" }}>Loading graph data…</p>;

  return (
    <div>
      <h1 style={{ fontSize: "1.4rem", marginBottom: "1rem" }}>Graph</h1>

      {vault && (
        <div style={{ display: "flex", gap: 12, marginBottom: "1.25rem", flexWrap: "wrap" }}>
          {[
            { label: "Nodes", value: vault.total_nodes },
            { label: "Link Nodes", value: vault.link_nodes },
            { label: "Edges", value: vault.total_edges },
          ].map((s) => (
            <div key={s.label} style={{ background: "#0d1117", borderRadius: 8, padding: "0.8rem 1.2rem", minWidth: 100 }}>
              <div style={{ fontSize: "1.4rem", fontWeight: 700, color: "#58a6ff" }}>{s.value}</div>
              <div style={{ fontSize: "0.78rem", color: "#8b949e" }}>{s.label}</div>
            </div>
          ))}
        </div>
      )}

      {vault && vault.top_links.length > 0 && (
        <>
          <h2 style={{ fontSize: "1rem", marginBottom: "0.5rem" }}>Top Cross-Domain Links</h2>
          {vault.top_links.map((l, i) => (
            <div key={i} style={{ fontSize: "0.85rem", color: "#c9d1d9", marginBottom: 4 }}>
              <span style={{ color: "#58a6ff", fontWeight: 600 }}>{l.node}</span>
              <span style={{ color: "#484f58" }}> — {l.domains.join(", ")} ({l.count} records)</span>
            </div>
          ))}
        </>
      )}

      <h2 style={{ fontSize: "1rem", marginTop: "1.25rem", marginBottom: "0.5rem" }}>
        Recall Graph — Recent Triples
      </h2>
      {triples.length === 0 ? (
        <p style={{ color: "#8b949e", fontSize: "0.88rem" }}>No triples in the Recall Graph yet.</p>
      ) : (
        triples.map((t, i) => (
          <div key={i} style={{ fontSize: "0.85rem", marginBottom: 4 }}>
            <span style={{ color: "#3fb950" }}>{t.subject}</span>
            <span style={{ color: "#d29922" }}> → {t.predicate} → </span>
            <span style={{ color: "#58a6ff" }}>{t.object}</span>
            {t.valid_from && <span style={{ color: "#484f58" }}> (from {t.valid_from})</span>}
          </div>
        ))
      )}
    </div>
  );
}
