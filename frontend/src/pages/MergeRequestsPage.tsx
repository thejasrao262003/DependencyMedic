import { useEffect, useState } from "react";
import { api } from "../services/api";
import type { MergeRequest } from "../types";

function badge(status: string) {
  const map: Record<string, string> = {
    open: "badge-open", merged: "badge-merged",
    closed: "badge-pending", draft: "badge-escalated",
  };
  return map[status] ?? "badge-pending";
}

function MRCard({ mr, onApprove }: { mr: MergeRequest; onApprove: (id: string) => void }) {
  const [approving, setApproving] = useState(false);

  const approve = async () => {
    setApproving(true);
    try { await api.post(`/merge-requests/${mr.id}/approve`, {}); onApprove(mr.id); }
    finally { setApproving(false); }
  };

  return (
    <div className="card card-hover p-5">
      <div className="flex items-start gap-4">
        <div className="flex-1 min-w-0 space-y-2">
          <div className="flex items-center gap-2.5 flex-wrap">
            <span className={`text-xs font-medium px-2.5 py-0.5 rounded-full ${badge(mr.status)}`}>
              {mr.status}
            </span>
            {mr.approved && (
              <span className="text-xs font-medium px-2.5 py-0.5 rounded-full badge-passed">
                ✓ approved
              </span>
            )}
          </div>
          <div className="text-black dark:text-white text-sm font-medium leading-snug">{mr.title}</div>
          <div className="text-xs font-mono text-gray-400 dark:text-gray-600">
            MR #{mr.gitlab_mr_id} · {mr.created_at.slice(0, 10)}
          </div>
          {mr.reviewers?.length > 0 && (
            <div className="text-xs text-gray-500 dark:text-gray-500">
              Reviewers: <span className="text-gray-700 dark:text-gray-300">{mr.reviewers.join(", ")}</span>
            </div>
          )}
          <div className="flex items-center gap-4 text-xs">
            {mr.mergeable && <span className="text-green-600 dark:text-green-400 font-medium">Mergeable</span>}
            {mr.approval_required && !mr.approved && (
              <span className="text-amber-700 dark:text-amber-400">Approval required</span>
            )}
          </div>
        </div>

        <div className="shrink-0 flex flex-col items-end gap-2">
          {mr.mr_url && (
            <a href={mr.mr_url} target="_blank" rel="noreferrer"
              className="text-xs text-gray-400 dark:text-gray-600 hover:text-black dark:hover:text-white transition-colors underline underline-offset-2 hover:no-underline">
              Open ↗
            </a>
          )}
          {mr.approval_required && !mr.approved && mr.status === "open" && (
            <button onClick={approve} disabled={approving} className="btn-primary text-xs">
              {approving ? "…" : "Approve"}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

export default function MergeRequestsPage() {
  const [mrs, setMrs] = useState<MergeRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("all");

  const fetch = () =>
    api.get("/merge-requests")
      .then((r) => setMrs(r.data.data ?? []))
      .catch(() => {})
      .finally(() => setLoading(false));

  useEffect(() => { fetch(); }, []);

  const onApprove = (id: string) =>
    setMrs((prev) => prev.map((m) => (m.id === id ? { ...m, approved: true } : m)));

  const statuses = ["all", ...Array.from(new Set(mrs.map((m) => m.status)))];
  const filtered = filter === "all" ? mrs : mrs.filter((m) => m.status === filter);
  const open = mrs.filter((m) => m.status === "open").length;

  return (
    <div className="space-y-6 fade-up">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-black dark:text-white">Merge Requests</h1>
          <p className="text-gray-500 dark:text-gray-400 text-sm mt-0.5">
            {open > 0 && <span className="text-green-600 dark:text-green-400 font-medium">{open} open · </span>}
            {mrs.length} total
          </p>
        </div>
        <button onClick={fetch} className="btn-ghost">⟳ Refresh</button>
      </div>

      {mrs.length > 0 && (
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
              {s}{s !== "all" && <span className="ml-1 text-gray-400 dark:text-gray-600">({mrs.filter(m=>m.status===s).length})</span>}
            </button>
          ))}
        </div>
      )}

      {loading ? (
        <div className="text-gray-400 dark:text-gray-600 text-sm">Loading...</div>
      ) : filtered.length === 0 ? (
        <div className="card p-8 text-center">
          <div className="text-gray-300 dark:text-gray-700 text-4xl mb-3">⤴</div>
          <div className="text-gray-500 dark:text-gray-400 text-sm">No merge requests yet.</div>
          <div className="text-gray-400 dark:text-gray-600 text-xs mt-1">Run the full pipeline to generate MRs</div>
        </div>
      ) : (
        <div className="space-y-2">
          {filtered.map((m) => <MRCard key={m.id} mr={m} onApprove={onApprove} />)}
        </div>
      )}
    </div>
  );
}
