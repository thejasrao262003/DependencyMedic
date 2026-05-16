import { useEffect, useState } from "react";
import { Routes, Route, NavLink } from "react-router-dom";
import DashboardPage from "./pages/DashboardPage";
import VulnerabilitiesPage from "./pages/VulnerabilitiesPage";
import VulnerabilityDetailPage from "./pages/VulnerabilityDetailPage";
import RepositoriesPage from "./pages/RepositoriesPage";
import RemediationsPage from "./pages/RemediationsPage";
import PipelinesPage from "./pages/PipelinesPage";
import MergeRequestsPage from "./pages/MergeRequestsPage";

const NAV = [
  { to: "/",               label: "Overview",       icon: "◈" },
  { to: "/vulnerabilities",label: "Vulnerabilities",icon: "⚠" },
  { to: "/repositories",   label: "Repositories",   icon: "⬡" },
  { to: "/remediations",   label: "Remediations",   icon: "⚙" },
  { to: "/pipelines",      label: "Pipelines",      icon: "▷" },
  { to: "/merge-requests", label: "Merge Requests", icon: "⤴" },
];

function NavItem({ to, label, icon }: { to: string; label: string; icon: string }) {
  return (
    <NavLink
      to={to}
      end={to === "/"}
      className={({ isActive }) =>
        `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all duration-150 ${
          isActive
            ? "bg-black text-white dark:bg-white dark:text-black"
            : "text-gray-500 hover:text-black hover:bg-gray-100 dark:text-gray-400 dark:hover:text-black dark:hover:bg-white/8"
        }`
      }
    >
      <span className="text-base w-5 text-center opacity-60">{icon}</span>
      <span className="font-medium">{label}</span>
    </NavLink>
  );
}

export default function App() {
  const [dark, setDark] = useState(() => {
    try { return localStorage.getItem("theme") !== "light"; } catch { return true; }
  });

  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
    try { localStorage.setItem("theme", dark ? "dark" : "light"); } catch {}
  }, [dark]);

  return (
    <div className="flex h-full bg-white dark:bg-[#0a0a0a]">
      {/* ── Sidebar ── */}
      <aside className="w-56 shrink-0 flex flex-col border-r border-gray-200 dark:border-[#272727] bg-white dark:bg-[#0a0a0a]">
        {/* Logo */}
        <div className="px-4 py-5 border-b border-gray-200 dark:border-[#272727]">
          <div className="flex items-center gap-2">
            <span className="text-xl">◈</span>
            <div>
              <div className="text-black dark:text-white font-semibold text-sm leading-tight">DependencyMedic</div>
              <div className="text-gray-400 dark:text-gray-600 text-xs mt-0.5">Autonomous Remediation</div>
            </div>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 px-3 py-4 space-y-0.5">
          {NAV.map((item) => (
            <NavItem key={item.to} {...item} />
          ))}
        </nav>

        {/* Footer */}
        <div className="px-4 py-3 border-t border-gray-200 dark:border-[#272727] flex items-center justify-between">
          <div className="text-xs text-gray-400 dark:text-gray-600 font-mono">v0.1.0 · hackathon</div>
          <button
            onClick={() => setDark((d) => !d)}
            title={dark ? "Switch to light mode" : "Switch to dark mode"}
            className="w-7 h-7 flex items-center justify-center rounded-md text-gray-400 hover:text-black dark:text-gray-500 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-white/8 transition-colors text-sm"
          >
            {dark ? "☀" : "☾"}
          </button>
        </div>
      </aside>

      {/* ── Main ── */}
      <main className="flex-1 overflow-auto bg-white dark:bg-[#0a0a0a]">
        <div className="max-w-5xl mx-auto px-6 py-8">
          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/vulnerabilities" element={<VulnerabilitiesPage />} />
            <Route path="/vulnerabilities/:id" element={<VulnerabilityDetailPage />} />
            <Route path="/repositories" element={<RepositoriesPage />} />
            <Route path="/remediations" element={<RemediationsPage />} />
            <Route path="/pipelines" element={<PipelinesPage />} />
            <Route path="/merge-requests" element={<MergeRequestsPage />} />
          </Routes>
        </div>
      </main>
    </div>
  );
}
