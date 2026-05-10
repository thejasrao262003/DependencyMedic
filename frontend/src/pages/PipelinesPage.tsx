import { useEffect, useState } from "react";
import { api } from "../services/api";
import type { PipelineRun } from "../types";

const STATUS_COLOR: Record<string, string> = {
  pending: "text-gray-400",
  running: "text-blue-400",
  passed: "text-green-400",
  failed: "text-red-400",
  cancelled: "text-orange-400",
};

export default function PipelinesPage() {
  const [pipelines, setPipelines] = useState<PipelineRun[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get("/pipelines")
      .then((r) => setPipelines(r.data.data ?? []))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="text-gray-400">Loading...</div>;

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-bold">Pipelines</h1>
      {pipelines.length === 0 ? (
        <div className="text-gray-500 text-sm">No pipeline runs yet.</div>
      ) : (
        <div className="space-y-3">
          {pipelines.map((p) => (
            <div key={p.id} className="bg-gray-900 border border-gray-800 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div className="font-mono text-sm text-gray-300">
                  Pipeline #{p.gitlab_pipeline_id}
                </div>
                <span className={`text-xs font-medium ${STATUS_COLOR[p.status] ?? "text-gray-400"}`}>
                  {p.status}
                </span>
              </div>
              {p.failed_stage && (
                <div className="text-red-400 text-xs mt-2">Failed: {p.failed_stage}</div>
              )}
              {p.failure_summary && (
                <div className="text-gray-400 text-xs mt-1">{p.failure_summary}</div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
