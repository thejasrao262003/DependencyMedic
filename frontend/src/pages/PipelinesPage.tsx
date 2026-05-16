import { useEffect, useState } from "react";
import { api } from "../services/api";
import type { PipelineRun } from "../types";

const ACTIVE = new Set(["pending", "running"]);

function badge(status: string) {
  const map: Record<string, string> = {
    pending: "badge-pending", running: "badge-running",
    passed: "badge-passed", failed: "badge-failed", cancelled: "badge-pending",
  };
  return map[status] ?? "badge-pending";
}

function fmt(s: number | null) {
  if (s == null) return "—";
  return s < 60 ? `${s}s` : `${Math.floor(s / 60)}m ${s % 60}s`;
}

export default function PipelinesPage() {
  const [pipelines, setPipelines] = useState<PipelineRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("all");

  const fetch = () =>
    api.get("/pipelines")
      .then((r) => setPipelines(r.data.data ?? []))
      .catch(() => {})
      .finally(() => setLoading(false));

  useEffect(() => { fetch(); }, []);

  useEffect(() => {
    if (!pipelines.some((p) => ACTIVE.has(p.status))) return;
    const id = setInterval(fetch, 4000);
    return () => clearInterval(id);
  }, [pipelines]);

  const statuses = ["all", ...Array.from(new Set(pipelines.map((p) => p.status)))];
  const filtered = filter === "all" ? pipelines : pipelines.filter((p) => p.status === filter);
  const passed = pipelines.filter((p) => p.status === "passed").length;
  const failed = pipelines.filter((p) => p.status === "failed").length;

  return (
    <div className="space-y-6 fade-up">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-black dark:text-white">Pipelines</h1>
          {pipelines.length > 0 && (
            <p className="text-gray-500 dark:text-gray-400 text-sm mt-0.5">
              <span className="text-green-600 dark:text-green-400 font-medium">{passed} passed</span>
              {" · "}
              <span className="text-red-600 dark:text-red-400 font-medium">{failed} failed</span>
              {" · "}
              {pipelines.length} total
            </p>
          )}
        </div>
        <button onClick={fetch} className="btn-ghost">⟳ Refresh</button>
      </div>

      {pipelines.length > 0 && (
        <div className="flex gap-2 flex-wrap">
          {statuses.map((s) => (
            <button
              key={s}
              onClick={() => setFilter(s)}
              className={`text-xs px-3 py-1.5 rounded-full border transition-all ${
                filter === s
                  ? "border-black dark:border-white text-black dark:text-white bg-gray-100 dark:bg-white/10 font-medium"
                  : "border-gray-200 dark:border-[#272727] text-gray-500 dark:text-gray-500 hover:text-gray-800 dark:hover:text-gray-200 hover:border-gray-300 dark:hover:border-gray-600"
              }`}
            >
              {s}
            </button>
          ))}
        </div>
      )}

      {loading ? (
        <div className="text-gray-400 dark:text-gray-600 text-sm">Loading...</div>
      ) : filtered.length === 0 ? (
        <div className="card p-8 text-center">
          <div className="text-gray-300 dark:text-gray-700 text-4xl mb-3">▷</div>
          <div className="text-gray-500 dark:text-gray-400 text-sm">No pipeline runs yet.</div>
        </div>
      ) : (
        <div className="space-y-2">
          {filtered.map((p) => (
            <div key={p.id} className="card card-hover p-4">
              <div className="flex items-start justify-between gap-4">
                <div className="space-y-1.5">
                  <div className="font-mono text-sm text-black dark:text-white">
                    Pipeline <span className="font-semibold">#{p.gitlab_pipeline_id}</span>
                  </div>
                  <div className="text-xs text-gray-400 dark:text-gray-600">
                    {p.created_at.slice(0, 16).replace("T", " ")}
                    {" · "}
                    <span className="font-mono">{fmt(p.duration_seconds)}</span>
                  </div>
                </div>
                <span className={`text-xs font-medium px-2.5 py-0.5 rounded-full shrink-0 ${badge(p.status)}`}>
                  {p.status}
                </span>
              </div>

              {p.status === "failed" && (
                <div className="mt-3 space-y-2">
                  {p.failed_stage && (
                    <div className="text-xs">
                      <span className="text-gray-400 dark:text-gray-500">Stage: </span>
                      <span className="font-mono text-red-600 dark:text-red-400">{p.failed_stage}</span>
                    </div>
                  )}
                  {p.failure_summary && (
                    <div className="text-xs font-mono text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-[#1e1e1e] rounded-lg p-2.5 whitespace-pre-wrap border border-gray-200 dark:border-[#272727]">
                      {p.failure_summary}
                    </div>
                  )}
                  {p.retry_attempted && (
                    <div className="text-xs text-amber-700 dark:text-amber-400">↺ Retry was attempted automatically</div>
                  )}
                </div>
              )}

              {p.logs_url && (
                <div className="mt-2">
                  <a href={p.logs_url} target="_blank" rel="noreferrer"
                    className="text-xs text-gray-400 dark:text-gray-600 hover:text-black dark:hover:text-white transition-colors underline underline-offset-2">
                    View CI logs ↗
                  </a>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
