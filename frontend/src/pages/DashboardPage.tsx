import { useEffect, useState } from "react";
import { api } from "../services/api";

function StatCard({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
      <div className={`text-3xl font-bold ${color}`}>{value}</div>
      <div className="text-gray-400 text-sm mt-1">{label}</div>
    </div>
  );
}

export default function DashboardPage() {
  const [stats, setStats] = useState({ vulns: 0, repos: 0, patches: 0, mrs: 0 });
  const [health, setHealth] = useState<Record<string, string>>({});

  useEffect(() => {
    Promise.all([
      api.get("/vulnerabilities?limit=1"),
      api.get("/repositories"),
      api.get("/remediations"),
      api.get("/merge-requests"),
      api.get("/health"),
    ])
      .then(([v, r, rem, m, h]) => {
        setStats({
          vulns: v.data.data?.total ?? 0,
          repos: (r.data.data as unknown[])?.length ?? 0,
          patches: (rem.data.data as unknown[])?.length ?? 0,
          mrs: (m.data.data as unknown[])?.length ?? 0,
        });
        setHealth(h.data.data?.services ?? {});
      })
      .catch(() => {});
  }, []);

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-bold">Overview</h1>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard label="Vulnerabilities" value={stats.vulns} color="text-red-400" />
        <StatCard label="Repositories" value={stats.repos} color="text-blue-400" />
        <StatCard label="Patch Attempts" value={stats.patches} color="text-yellow-400" />
        <StatCard label="Merge Requests" value={stats.mrs} color="text-green-400" />
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
        <h2 className="text-sm font-semibold text-gray-400 mb-4 uppercase tracking-wide">
          Service Health
        </h2>
        <div className="flex gap-4 flex-wrap">
          {Object.entries(health).map(([svc, status]) => (
            <div key={svc} className="flex items-center gap-2 text-sm">
              <span
                className={`w-2 h-2 rounded-full ${status === "healthy" ? "bg-green-400" : "bg-red-400"}`}
              />
              <span className="text-gray-300">{svc}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
