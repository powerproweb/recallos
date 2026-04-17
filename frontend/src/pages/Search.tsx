import { useEffect, useState, FormEvent } from "react";
import { apiGet, apiPost } from "../api/client";

interface SearchResult {
  text: string;
  domain: string;
  node: string;
  source_file: string;
  similarity: number;
}

interface SearchResponse {
  query: string;
  filters: { domain: string | null; node: string | null };
  results: SearchResult[];
  error?: string;
}

interface FiltersResponse {
  domains: Record<string, number>;
  nodes: Record<string, number>;
}

const SIMILARITY_COLOR = (s: number) =>
  s >= 0.85 ? "#3fb950" : s >= 0.65 ? "#d29922" : "#8b949e";

export default function Search() {
  const [query, setQuery] = useState("");
  const [domain, setDomain] = useState("");
  const [node, setNode] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [searched, setSearched] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Filter options
  const [domains, setDomains] = useState<string[]>([]);
  const [nodes, setNodes] = useState<string[]>([]);

  useEffect(() => {
    apiGet<FiltersResponse>("/api/search/filters")
      .then((f) => {
        setDomains(Object.keys(f.domains).sort());
        setNodes(Object.keys(f.nodes).sort());
      })
      .catch(() => {});
  }, []);

  const handleSearch = (e: FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError(null);
    setSearched(true);

    apiPost<SearchResponse>("/api/search", {
      query: query.trim(),
      domain: domain || null,
      node: node || null,
      limit: 10,
    })
      .then((res) => {
        if (res.error) {
          setError(res.error);
          setResults([]);
        } else {
          setResults(res.results || []);
        }
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  };

  return (
    <div>
      <h1 style={{ fontSize: "1.4rem", marginBottom: "1rem" }}>Search</h1>

      {/* Search form */}
      <form onSubmit={handleSearch} style={{ marginBottom: "1.25rem" }}>
        <div style={{ display: "flex", gap: 8, marginBottom: 10 }}>
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="What are you looking for?"
            style={{
              flex: 1,
              padding: "0.55rem 0.75rem",
              background: "#0d1117",
              border: "1px solid #30363d",
              borderRadius: 6,
              color: "#c9d1d9",
              fontSize: "0.95rem",
              outline: "none",
            }}
          />
          <button
            type="submit"
            disabled={loading || !query.trim()}
            style={{
              padding: "0.55rem 1.25rem",
              background: "#238636",
              color: "#fff",
              border: "none",
              borderRadius: 6,
              fontSize: "0.9rem",
              cursor: loading ? "wait" : "pointer",
              opacity: !query.trim() ? 0.5 : 1,
            }}
          >
            {loading ? "Searching..." : "Search"}
          </button>
        </div>

        {/* Filters */}
        <div style={{ display: "flex", gap: 8 }}>
          <select
            value={domain}
            onChange={(e) => setDomain(e.target.value)}
            style={{
              padding: "0.4rem 0.6rem",
              background: "#0d1117",
              border: "1px solid #30363d",
              borderRadius: 6,
              color: "#8b949e",
              fontSize: "0.82rem",
            }}
          >
            <option value="">All domains</option>
            {domains.map((d) => (
              <option key={d} value={d}>
                {d}
              </option>
            ))}
          </select>
          <select
            value={node}
            onChange={(e) => setNode(e.target.value)}
            style={{
              padding: "0.4rem 0.6rem",
              background: "#0d1117",
              border: "1px solid #30363d",
              borderRadius: 6,
              color: "#8b949e",
              fontSize: "0.82rem",
            }}
          >
            <option value="">All nodes</option>
            {nodes.map((n) => (
              <option key={n} value={n}>
                {n}
              </option>
            ))}
          </select>
        </div>
      </form>

      {/* Error */}
      {error && (
        <p style={{ color: "#f85149", marginBottom: "1rem" }}>
          Error: {error}
        </p>
      )}

      {/* Results */}
      {searched && !loading && !error && results.length === 0 && (
        <p style={{ color: "#8b949e" }}>No results found.</p>
      )}

      {results.map((r, i) => (
        <div
          key={i}
          style={{
            background: "#0d1117",
            borderRadius: 8,
            padding: "0.9rem 1rem",
            marginBottom: 10,
          }}
        >
          {/* Header row */}
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "baseline",
              marginBottom: 6,
            }}
          >
            <div style={{ fontSize: "0.85rem" }}>
              <span style={{ color: "#58a6ff", fontWeight: 600 }}>
                {r.domain}
              </span>
              <span style={{ color: "#484f58", margin: "0 6px" }}>/</span>
              <span style={{ color: "#8b949e" }}>{r.node}</span>
            </div>
            <span
              style={{
                fontSize: "0.78rem",
                fontWeight: 600,
                color: SIMILARITY_COLOR(r.similarity),
              }}
            >
              {(r.similarity * 100).toFixed(1)}%
            </span>
          </div>

          {/* Source */}
          <div
            style={{ fontSize: "0.78rem", color: "#484f58", marginBottom: 8 }}
          >
            {r.source_file}
          </div>

          {/* Content preview */}
          <pre
            style={{
              fontSize: "0.82rem",
              color: "#c9d1d9",
              whiteSpace: "pre-wrap",
              wordBreak: "break-word",
              margin: 0,
              lineHeight: 1.5,
              maxHeight: 200,
              overflow: "auto",
            }}
          >
            {r.text}
          </pre>
        </div>
      ))}
    </div>
  );
}
