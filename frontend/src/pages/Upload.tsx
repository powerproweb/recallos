import { useState, useCallback, useEffect, DragEvent, ChangeEvent } from "react";
import { apiFetch, apiGet } from "../api/client";

interface Job {
  id: number;
  type: string;
  status: string;
  params: string;
  result: string | null;
  created_at: string;
  updated_at: string;
}

const STATUS_COLORS: Record<string, string> = {
  pending: "#d29922",
  running: "#58a6ff",
  done: "#3fb950",
  failed: "#f85149",
};

export default function Upload() {
  const [files, setFiles] = useState<File[]>([]);
  const [domain, setDomain] = useState("uploads");
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [jobs, setJobs] = useState<Job[]>([]);

  // Load recent jobs on mount and after upload
  const loadJobs = useCallback(() => {
    apiGet<{ jobs: Job[] }>("/api/jobs?limit=10")
      .then((res) => setJobs(res.jobs || []))
      .catch(() => {});
  }, []);

  useEffect(() => {
    loadJobs();
    const interval = setInterval(loadJobs, 3000);
    return () => clearInterval(interval);
  }, [loadJobs]);

  const addFiles = (newFiles: FileList | File[]) => {
    setFiles((prev) => [...prev, ...Array.from(newFiles)]);
    setMessage(null);
  };

  const handleDrop = (e: DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files.length) addFiles(e.dataTransfer.files);
  };

  const handleFileInput = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.length) addFiles(e.target.files);
  };

  const handleUpload = async () => {
    if (!files.length) return;
    setUploading(true);
    setMessage(null);

    const formData = new FormData();
    files.forEach((f) => formData.append("files", f));
    formData.append("domain", domain);

    try {
      const res = await apiFetch("/api/upload", { method: "POST", body: formData });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setMessage(`Job #${data.job_id} created — ${data.files_received} file(s) queued for ingest.`);
      setFiles([]);
      loadJobs();
    } catch (err: any) {
      setMessage(`Error: ${err.message}`);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div>
      <h1 style={{ fontSize: "1.4rem", marginBottom: "1rem" }}>Upload</h1>

      {/* Drop zone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        style={{
          border: `2px dashed ${dragOver ? "#58a6ff" : "#30363d"}`,
          borderRadius: 8,
          padding: "2rem",
          textAlign: "center",
          background: dragOver ? "#161b22" : "#0d1117",
          marginBottom: "1rem",
          cursor: "pointer",
          transition: "border-color 0.15s, background 0.15s",
        }}
        onClick={() => document.getElementById("file-input")?.click()}
      >
        <input
          id="file-input"
          type="file"
          multiple
          style={{ display: "none" }}
          onChange={handleFileInput}
        />
        <p style={{ color: "#8b949e", margin: 0 }}>
          {dragOver ? "Drop files here" : "Drag & drop files, or click to browse"}
        </p>
      </div>

      {/* Selected files */}
      {files.length > 0 && (
        <div style={{ marginBottom: "1rem" }}>
          <div style={{ fontSize: "0.85rem", color: "#c9d1d9", marginBottom: 6 }}>
            {files.length} file(s) selected:
          </div>
          {files.map((f, i) => (
            <div key={i} style={{ fontSize: "0.82rem", color: "#8b949e", paddingLeft: 8 }}>
              {f.name} ({(f.size / 1024).toFixed(1)} KB)
            </div>
          ))}
        </div>
      )}

      {/* Domain + upload button */}
      <div style={{ display: "flex", gap: 8, marginBottom: "1rem", alignItems: "center" }}>
        <input
          type="text"
          value={domain}
          onChange={(e) => setDomain(e.target.value)}
          placeholder="Domain name"
          style={{
            padding: "0.45rem 0.65rem",
            background: "#0d1117",
            border: "1px solid #30363d",
            borderRadius: 6,
            color: "#c9d1d9",
            fontSize: "0.88rem",
            width: 180,
          }}
        />
        <button
          onClick={handleUpload}
          disabled={uploading || !files.length}
          style={{
            padding: "0.45rem 1.1rem",
            background: "#238636",
            color: "#fff",
            border: "none",
            borderRadius: 6,
            fontSize: "0.88rem",
            cursor: uploading ? "wait" : "pointer",
            opacity: !files.length ? 0.5 : 1,
          }}
        >
          {uploading ? "Uploading..." : "Upload & Ingest"}
        </button>
      </div>

      {/* Status message */}
      {message && (
        <p style={{ color: message.startsWith("Error") ? "#f85149" : "#3fb950", fontSize: "0.88rem" }}>
          {message}
        </p>
      )}

      {/* Recent jobs */}
      {jobs.length > 0 && (
        <>
          <h2 style={{ fontSize: "1rem", marginTop: "1.5rem", marginBottom: "0.6rem" }}>
            Recent Jobs
          </h2>
          {jobs.map((job) => (
            <div
              key={job.id}
              style={{
                background: "#0d1117",
                borderRadius: 8,
                padding: "0.7rem 1rem",
                marginBottom: 8,
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                fontSize: "0.85rem",
              }}
            >
              <div>
                <span style={{ color: "#c9d1d9" }}>#{job.id}</span>
                <span style={{ color: "#484f58", margin: "0 8px" }}>·</span>
                <span style={{ color: "#8b949e" }}>{job.type}</span>
              </div>
              <span
                style={{
                  fontWeight: 600,
                  color: STATUS_COLORS[job.status] || "#8b949e",
                  fontSize: "0.8rem",
                  textTransform: "uppercase",
                }}
              >
                {job.status}
              </span>
            </div>
          ))}
        </>
      )}
    </div>
  );
}
