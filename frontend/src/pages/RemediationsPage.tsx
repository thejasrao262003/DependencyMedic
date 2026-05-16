import { useEffect, useState } from "react";
import { api } from "../services/api";
import type { PatchAttempt } from "../types";

const ACTIVE = new Set(["pending", "generating", "validating"]);

function badge(status: string) {
  const map: Record<string, string> = {
    pending: "badge-pending", generating: "badge-running", generated: "badge-running",
    validating: "badge-running", validated: "badge-validated",
    failed: "badge-failed", escalated: "badge-escalated",
  };
  return map[status] ?? "badge-pending";
}

function PatchCard({ patch }: { patch: PatchAttempt }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="card card-hover overflow-hidden">
      <button className="w-full p-4 text-left" onClick={() => setOpen((v) => !v)}>
        <div className="flex items-center justify-between gap-4">
          <div className="min-w-0">
            <div className="font-mono text-sm text-black dark:text-white truncate">{patch.branch_name}</div>
            <div className="text-xs text-gray-400 dark:text-gray-600 mt-0.5">
              Attempt #{patch.attempt_number} · {patch.created_at.slice(0, 10)}
            </div>
          </div>
          <div className="flex items-center gap-3 shrink-0">
            {patch.confidence_score != null && (
              <span className="text-xs font-mono text-gray-400 dark:text-gray-600">
                {(patch.confidence_score * 100).toFixed(0)}%
              </span>
            )}
            <span className={`text-xs font-medium px-2.5 py-0.5 rounded-full ${badge(patch.status)}`}>
              {patch.status}
            </span>
            <span className="text-gray-400 dark:text-gray-600 text-xs">{open ? "▲" : "▼"}</span>
          </div>
        </div>
        {patch.patch_summary && (
          <div className="text-xs text-gray-400 dark:text-gray-500 mt-2 truncate">{patch.patch_summary}</div>
        )}
      </button>

      {open && (
        <div className="border-t border-gray-200 dark:border-[#272727] px-4 py-3 space-y-3 text-sm">
          {patch.dependency_changes?.length > 0 && (
            <div>
              <div className="text-xs text-gray-400 dark:text-gray-500 uppercase tracking-wide mb-2">Dependency Changes</div>
              {patch.dependency_changes.map((c, i) => (
                <div key={i} className="flex items-center gap-2 font-mono text-xs py-0.5">
                  <span className="text-gray-600 dark:text-gray-400 w-32 truncate">{c.package}</span>
                  <span className="text-red-600 dark:text-red-400">{c.from_version}</span>
                  <span className="text-gray-300 dark:text-gray-700">→</span>
                  <span className="text-green-600 dark:text-green-400">{c.to_version}</span>
                </div>
              ))}
            </div>
          )}
          {patch.retry_reason && (
            <div>
              <div className="text-xs text-gray-400 dark:text-gray-500 uppercase tracking-wide mb-1">Retry Reason</div>
              <div className="text-xs text-amber-700 dark:text-amber-400">{patch.retry_reason}</div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function RemediationsPage() {
  const [patches, setPatches] = useState<PatchAttempt[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("all");
  const [triggering, setTriggering] = useState(false);

  const fetch = () =>
    api.get("/remediations")
      .then((r) => setPatches(r.data.data ?? []))
      .catch(() => {})
      .finally(() => setLoading(false));

  useEffect(() => { fetch(); }, []);

  useEffect(() => {
    if (!patches.some((p) => ACTIVE.has(p.status))) return;
    const id = setInterval(fetch, 5000);
    return () => clearInterval(id);
  }, [patches]);

  const trigger = async () => {
    setTriggering(true);
    try { await api.post("/remediations/generate", {}); await fetch(); }
    finally { setTriggering(false); }
  };

  const statuses = ["all", ...Array.from(new Set(patches.map((p) => p.status)))];
  const filtered = filter === "all" ? patches : patches.filter((p) => p.status === filter);

  return (
    <div className="space-y-6 fade-up">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-black dark:text-white">Remediations</h1>
          <p className="text-gray-500 dark:text-gray-400 text-sm mt-0.5">{patches.length} patch attempts</p>
        </div>
        <div className="flex gap-2">
          <button onClick={fetch} className="btn-ghost">⟳</button>
          <button onClick={trigger} disabled={triggering} className="btn-primary">
            {triggering ? "Triggering…" : "Trigger Remediation"}
          </button>
        </div>
      </div>

      {patches.length > 0 && (
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
              {s}{s !== "all" && <span className="ml-1 text-gray-400 dark:text-gray-600">({patches.filter(p=>p.status===s).length})</span>}
            </button>
          ))}
        </div>
      )}

      {loading ? (
        <div className="text-gray-400 dark:text-gray-600 text-sm">Loading...</div>
      ) : filtered.length === 0 ? (
        <div className="card p-8 text-center">
          <div className="text-gray-300 dark:text-gray-700 text-4xl mb-3">⚙</div>
          <div className="text-gray-500 dark:text-gray-400 text-sm">No patch attempts yet.</div>
          <div className="text-gray-400 dark:text-gray-600 text-xs mt-1">Trigger the pipeline to generate patches</div>
        </div>
      ) : (
        <div className="space-y-2">
          {filtered.map((p) => <PatchCard key={p.id} patch={p} />)}
        </div>
      )}
    </div>
  );
}
