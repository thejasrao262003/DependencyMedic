import { useEffect, useState } from "react";
import { api } from "../services/api";
import type { Vulnerability } from "../types";

const SEVERITY_COLOR: Record<string, string> = {
  critical: "text-red-400 bg-red-900/30",
  high: "text-orange-400 bg-orange-900/30",
  medium: "text-yellow-400 bg-yellow-900/30",
  low: "text-green-400 bg-green-900/30",
};

interface IngestResult {
  total_fetched: number;
  new_stored: number;
  updated: number;
  events_published: number;
  errors: string[];
}

export default function VulnerabilitiesPage() {
  const [vulns, setVulns] = useState<Vulnerability[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [ingesting, setIngesting] = useState(false);
  const [ingestResult, setIngestResult] = useState<IngestResult | null>(null);
  const [ingestError, setIngestError] = useState<string | null>(null);
  const [severityFilter, setSeverityFilter] = useState("");

  const fetchVulns = (severity = "") => {
    setLoading(true);
    const params = severity ? `?severity=${severity}&limit=50` : "?limit=50";
    api
      .get(`/vulnerabilities${params}`)
      .then((r) => {
        setVulns(r.data.data?.items ?? []);
        setTotal(r.data.data?.total ?? 0);
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchVulns(severityFilter);
  }, [severityFilter]);

  const runIngest = async () => {
    setIngesting(true);
    setIngestResult(null);
    setIngestError(null);
    try {
      const r = await api.post("/vulnerabilities/ingest", {
        days_back: 30,
        severities: ["CRITICAL", "HIGH"],
        packages: [
          { name: "log4j-core", ecosystem: "Maven" },
          { name: "cryptography", ecosystem: "PyPI" },
          { name: "Pillow", ecosystem: "PyPI" },
          { name: "PyYAML", ecosystem: "PyPI" },
          { name: "requests", ecosystem: "PyPI" },
        ],
      });
      setIngestResult(r.data.data);
      fetchVulns(severityFilter);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Ingest request failed";
      setIngestError(msg);
    } finally {
      setIngesting(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold">Vulnerabilities {total > 0 && <span className="text-gray-400 text-base font-normal">({total})</span>}</h1>
        <button
          onClick={runIngest}
          disabled={ingesting}
          className="text-sm px-4 py-2 rounded bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
        >
          {ingesting ? "Ingesting…" : "Ingest CVEs"}
        </button>
      </div>

      {ingestError && (
        <div className="bg-gray-900 border border-red-800 rounded-lg p-4 text-sm text-red-400">
          Ingest failed: {ingestError}
        </div>
      )}

      {ingestResult && (
        <div className="bg-gray-900 border border-green-800 rounded-lg p-4 text-sm">
          <div className="text-green-400 font-medium mb-2">Ingestion complete</div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-center">
            <div><div className="text-white font-bold text-lg">{ingestResult.total_fetched}</div><div className="text-gray-400 text-xs">fetched</div></div>
            <div><div className="text-green-400 font-bold text-lg">{ingestResult.new_stored}</div><div className="text-gray-400 text-xs">new</div></div>
            <div><div className="text-yellow-400 font-bold text-lg">{ingestResult.updated}</div><div className="text-gray-400 text-xs">updated</div></div>
            <div><div className="text-blue-400 font-bold text-lg">{ingestResult.events_published}</div><div className="text-gray-400 text-xs">events published</div></div>
          </div>
          {ingestResult.errors.length > 0 && (
            <div className="mt-2 text-red-400 text-xs">{ingestResult.errors.length} errors</div>
          )}
        </div>
      )}

      <div className="flex gap-2">
        {["", "critical", "high", "medium", "low"].map((s) => (
          <button
            key={s}
            onClick={() => setSeverityFilter(s)}
            className={`text-xs px-3 py-1 rounded transition-colors ${
              severityFilter === s
                ? "bg-blue-600 text-white"
                : "bg-gray-800 text-gray-400 hover:text-white"
            }`}
          >
            {s === "" ? "All" : s.charAt(0).toUpperCase() + s.slice(1)}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="text-gray-400">Loading...</div>
      ) : vulns.length === 0 ? (
        <div className="text-gray-500 text-sm">
          No vulnerabilities found. Click <span className="text-blue-400">Ingest CVEs</span> to fetch from NVD + OSV.
        </div>
      ) : (
        <div className="space-y-3">
          {vulns.map((v) => (
            <div key={v.id} className="bg-gray-900 border border-gray-800 rounded-lg p-4">
              <div className="flex items-start justify-between gap-4">
                <div className="min-w-0">
                  <div className="font-mono text-blue-400 text-sm">{v.cve_id}</div>
                  <div className="text-white mt-1 text-sm">{v.summary}</div>
                  {v.affected_packages.length > 0 && (
                    <div className="flex gap-2 mt-2 flex-wrap">
                      {v.affected_packages.map((pkg, i) => (
                        <span key={i} className="text-xs bg-gray-800 text-gray-300 px-2 py-0.5 rounded font-mono">
                          {pkg.name}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
                <div className="flex flex-col items-end gap-1 shrink-0">
                  <span className={`text-xs px-2 py-1 rounded font-medium ${SEVERITY_COLOR[v.severity] ?? "text-gray-400"}`}>
                    {v.severity}
                  </span>
                  {v.cvss_score != null && (
                    <span className="text-xs text-gray-500">CVSS {v.cvss_score}</span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
