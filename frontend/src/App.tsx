import { Routes, Route, NavLink } from "react-router-dom";
import DashboardPage from "./pages/DashboardPage";
import VulnerabilitiesPage from "./pages/VulnerabilitiesPage";
import RepositoriesPage from "./pages/RepositoriesPage";
import RemediationsPage from "./pages/RemediationsPage";
import PipelinesPage from "./pages/PipelinesPage";

function NavItem({ to, label }: { to: string; label: string }) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        `px-4 py-2 rounded text-sm font-medium transition-colors ${
          isActive ? "bg-blue-600 text-white" : "text-gray-400 hover:text-white"
        }`
      }
    >
      {label}
    </NavLink>
  );
}

export default function App() {
  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-gray-800 px-6 py-4 flex items-center gap-6">
        <span className="text-lg font-bold text-white">
          DependencyMedic
        </span>
        <nav className="flex gap-2">
          <NavItem to="/" label="Dashboard" />
          <NavItem to="/vulnerabilities" label="Vulnerabilities" />
          <NavItem to="/repositories" label="Repositories" />
          <NavItem to="/remediations" label="Remediations" />
          <NavItem to="/pipelines" label="Pipelines" />
        </nav>
      </header>
      <main className="flex-1 p-6">
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/vulnerabilities" element={<VulnerabilitiesPage />} />
          <Route path="/repositories" element={<RepositoriesPage />} />
          <Route path="/remediations" element={<RemediationsPage />} />
          <Route path="/pipelines" element={<PipelinesPage />} />
        </Routes>
      </main>
    </div>
  );
}
