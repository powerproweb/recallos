import { Routes, Route, NavLink } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import Search from "./pages/Search";
import Upload from "./pages/Upload";
import Download from "./pages/Download";
import Graph from "./pages/Graph";
import Network from "./pages/Network";
import Models from "./pages/Models";
import Support from "./pages/Support";
import MCP from "./pages/MCP";
import Settings from "./pages/Settings";

const NAV_ITEMS = [
  { to: "/", label: "Dashboard" },
  { to: "/search", label: "Search" },
  { to: "/upload", label: "Upload" },
  { to: "/download", label: "Export" },
  { to: "/graph", label: "Graph" },
  { to: "/network", label: "Network" },
  { to: "/models", label: "Models" },
  { to: "/support", label: "Support" },
  { to: "/mcp", label: "MCP" },
  { to: "/settings", label: "Settings" },
];

export default function App() {
  return (
    <div style={{ display: "flex", height: "100vh" }}>
      {/* Sidebar */}
      <nav
        style={{
          width: 220,
          background: "#0f1117",
          color: "#c9d1d9",
          padding: "1.5rem 0",
          display: "flex",
          flexDirection: "column",
          gap: 2,
          flexShrink: 0,
        }}
      >
        <div
          style={{
            padding: "0 1.25rem 1rem",
            fontSize: "1.1rem",
            fontWeight: 700,
            letterSpacing: "0.03em",
          }}
        >
          RecallOS
        </div>
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === "/"}
            style={({ isActive }) => ({
              display: "block",
              padding: "0.55rem 1.25rem",
              color: isActive ? "#fff" : "#8b949e",
              background: isActive ? "#1c2030" : "transparent",
              textDecoration: "none",
              fontSize: "0.9rem",
              borderLeft: isActive ? "3px solid #58a6ff" : "3px solid transparent",
            })}
          >
            {item.label}
          </NavLink>
        ))}
      </nav>

      {/* Main content */}
      <main style={{ flex: 1, overflow: "auto", padding: "1.5rem", background: "#161b22" }}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/search" element={<Search />} />
          <Route path="/upload" element={<Upload />} />
          <Route path="/download" element={<Download />} />
          <Route path="/graph" element={<Graph />} />
          <Route path="/network" element={<Network />} />
          <Route path="/models" element={<Models />} />
          <Route path="/support" element={<Support />} />
          <Route path="/mcp" element={<MCP />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </main>
    </div>
  );
}
