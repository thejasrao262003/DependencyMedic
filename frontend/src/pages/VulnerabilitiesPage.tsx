import { useEffect, useState } from "react";
import { api } from "../services/api";
import type { Vulnerability } from "../types";

const SEVERITY_COLOR: Record<string, string> = {
  critical: "text-red-400 bg-red-900/30",
  high: "text-orange-400 bg-orange-900/30",
  medium: "text-yellow-400 bg-yellow-900/30",
  low: "text-green-400 bg-green-900/30",
};

export default function VulnerabilitiesPage() {
  const [vulns, setVulns] = useState<Vulnerability[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get("/vulnerabilities")
      .then((r) => setVulns(r.data.data?.items ?? []))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="text-gray-400">Loading...</div>;

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-bold">Vulnerabilities</h1>
      {vulns.length === 0 ? (
        <div className="text-gray-500 text-sm">
          No vulnerabilities found. Run <code className="text-blue-400">make seed-demo</code> to load demo data.
        </div>
      ) : (
        <div className="space-y-3">
          {vulns.map((v) => (
            <div key={v.id} className="bg-gray-900 border border-gray-800 rounded-lg p-4">
              <div className="flex items-start justify-between">
                <div>
                  <div className="font-mono text-blue-400 text-sm">{v.cve_id}</div>
                  <div className="text-white mt-1">{v.summary}</div>
                  {v.cvss_score && (
                    <div className="text-gray-400 text-xs mt-1">CVSS {v.cvss_score}</div>
                  )}
                </div>
                <span
                  className={`text-xs px-2 py-1 rounded font-medium ${SEVERITY_COLOR[v.severity] ?? "text-gray-400"}`}
                >
                  {v.severity}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
