import { useEffect, useState } from "react";
import { api } from "../services/api";

function StatCard({ label, value, sub }: { label: string; value: number | string; sub?: string }) {
  return (
    <div className="card card-hover p-5 fade-up">
      <div className="text-3xl font-bold font-mono text-black dark:text-white">{value}</div>
      <div className="text-gray-500 dark:text-gray-400 text-sm mt-1 font-medium">{label}</div>
      {sub && <div className="text-gray-400 dark:text-gray-600 text-xs mt-0.5">{sub}</div>}
    </div>
  );
}

function ServiceDot({ name, status }: { name: string; status: string }) {
  const ok = status === "healthy";
  return (
    <div className="flex items-center gap-2 py-2 px-3 rounded-lg bg-gray-50 dark:bg-[#1e1e1e] border border-gray-100 dark:border-[#272727]">
      <span className={`w-2 h-2 rounded-full ${ok ? "bg-green-500" : "bg-red-500"} ${ok ? "dot-pulse" : ""}`} />
      <span className="text-sm text-gray-700 dark:text-gray-300">{name}</span>
      <span className={`ml-auto text-xs font-medium ${ok ? "text-green-600 dark:text-green-400" : "text-red-600 dark:text-red-400"}`}>
        {status}
      </span>
    </div>
  );
}

const PIPELINE_STEPS = [
  "CVE Ingested",
  "Repo Matched",
  "Risk Scored",
  "Patch Generated",
  "CI Recovery",
  "MR Created",
];

export default function DashboardPage() {
  const [stats, setStats] = useState({ vulns: 0, repos: 0, patches: 0, mrs: 0 });
  const [health, setHealth] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);

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
          vulns:   v.data.data?.total ?? 0,
          repos:   (r.data.data as unknown[])?.length ?? 0,
          patches: (rem.data.data as unknown[])?.length ?? 0,
          mrs:     (m.data.data as unknown[])?.length ?? 0,
        });
        setHealth(h.data.data?.services ?? {});
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold text-black dark:text-white">Mission Control</h1>
        <p className="text-gray-500 dark:text-gray-400 text-sm mt-1">Autonomous vulnerability remediation status</p>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Vulnerabilities" value={loading ? "—" : stats.vulns}  sub="tracked CVEs" />
        <StatCard label="Repositories"   value={loading ? "—" : stats.repos}  sub="monitored" />
        <StatCard label="Patch Attempts" value={loading ? "—" : stats.patches} sub="generated" />
        <StatCard label="Merge Requests" value={loading ? "—" : stats.mrs}    sub="awaiting review" />
      </div>

      <div className="card p-6">
        <h2 className="text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-widest mb-4">
          Autonomous Pipeline
        </h2>
        <div className="flex items-center gap-2 flex-wrap">
          {PIPELINE_STEPS.map((label, i) => (
            <>
              <span
                key={label}
                className="text-xs font-medium px-2.5 py-1 rounded-full border border-gray-200 dark:border-[#333] bg-gray-50 dark:bg-[#1e1e1e] text-gray-700 dark:text-gray-300"
              >
                {label}
              </span>
              {i < PIPELINE_STEPS.length - 1 && (
                <span key={`arrow-${i}`} className="text-gray-300 dark:text-gray-700 text-sm">→</span>
              )}
            </>
          ))}
        </div>
      </div>

      <div className="card p-6">
        <h2 className="text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-widest mb-4">
          Service Health
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
          {Object.keys(health).length === 0
            ? <div className="text-gray-400 dark:text-gray-600 text-sm">Loading services...</div>
            : Object.entries(health).map(([svc, status]) => (
                <ServiceDot key={svc} name={svc} status={status} />
              ))
          }
        </div>
      </div>
    </div>
  );
}
