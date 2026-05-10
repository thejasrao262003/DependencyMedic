import { useEffect, useState } from "react";
import { api } from "../services/api";
import type { PatchAttempt } from "../types";

const STATUS_COLOR: Record<string, string> = {
  pending: "text-gray-400",
  generating: "text-blue-400",
  generated: "text-blue-300",
  validating: "text-yellow-400",
  validated: "text-green-400",
  failed: "text-red-400",
  escalated: "text-orange-400",
};

export default function RemediationsPage() {
  const [patches, setPatches] = useState<PatchAttempt[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get("/remediations")
      .then((r) => setPatches(r.data.data ?? []))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="text-gray-400">Loading...</div>;

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-bold">Remediations</h1>
      {patches.length === 0 ? (
        <div className="text-gray-500 text-sm">No patch attempts yet.</div>
      ) : (
        <div className="space-y-3">
          {patches.map((p) => (
            <div key={p.id} className="bg-gray-900 border border-gray-800 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div className="font-mono text-sm text-gray-300">{p.branch_name}</div>
                <span className={`text-xs font-medium ${STATUS_COLOR[p.status] ?? "text-gray-400"}`}>
                  {p.status}
                </span>
              </div>
              <div className="text-gray-400 text-xs mt-2">Attempt #{p.attempt_number}</div>
              {p.confidence_score != null && (
                <div className="text-gray-400 text-xs">
                  Confidence: {(p.confidence_score * 100).toFixed(0)}%
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
