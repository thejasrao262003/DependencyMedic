import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../services/api";
import type { Vulnerability } from "../types";

const SEVERITIES = ["", "critical", "high", "medium", "low"] as const;

function SeverityBadge({ s }: { s: string }) {
  return (
    <span className={`text-xs font-medium px-2 py-0.5 rounded-full badge-${s}`}>
      {s}
    </span>
  );
}

export default function VulnerabilitiesPage() {
  const navigate = useNavigate();
  const [vulns, setVulns] = useState<Vulnerability[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [ingesting, setIngesting] = useState(false);
  const [ingestResult, setIngestResult] = useState<Record<string, number> | null>(null);
  const [severity, setSeverity] = useState("");

  const fetchVulns = (sev = "") => {
    setLoading(true);
    const q = sev ? `?severity=${sev}&limit=50` : "?limit=50";
    api.get(`/vulnerabilities${q}`)
      .then((r) => { setVulns(r.data.data?.items ?? []); setTotal(r.data.data?.total ?? 0); })
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchVulns(severity); }, [severity]);

  const runIngest = async () => {
    setIngesting(true);
    setIngestResult(null);
    try {
      const r = await api.post("/vulnerabilities/ingest", {
        days_back: 30,
        severities: ["CRITICAL", "HIGH"],
        packages: [
          { name: "requests", ecosystem: "PyPI" },
          { name: "cryptography", ecosystem: "PyPI" },
          { name: "Pillow", ecosystem: "PyPI" },
        ],
      });
      setIngestResult(r.data.data);
      fetchVulns(severity);
    } finally {
      setIngesting(false);
    }
  };

  return (
    <div className="space-y-6 fade-up">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-black dark:text-white">Vulnerabilities</h1>
          <p className="text-gray-500 dark:text-gray-400 text-sm mt-0.5">{total} CVEs tracked</p>
        </div>
        <button onClick={runIngest} disabled={ingesting} className="btn-primary">
          {ingesting ? "Scanning…" : "⟳ Ingest CVEs"}
        </button>
      </div>

      {ingestResult && (
        <div className="card p-4" style={{ borderColor: "#bbf7d0" }}>
          <div className="text-green-700 dark:text-green-400 text-sm font-medium mb-3">Ingestion complete</div>
          <div className="grid grid-cols-4 gap-4 text-center">
            {[
              { v: ingestResult.total_fetched,    l: "fetched" },
              { v: ingestResult.new_stored,        l: "new" },
              { v: ingestResult.updated,           l: "updated" },
              { v: ingestResult.matched_published, l: "matched" },
            ].map(({ v, l }) => (
              <div key={l}>
                <div className="text-xl font-bold font-mono text-black dark:text-white">{v ?? 0}</div>
                <div className="text-xs text-gray-400 dark:text-gray-500 mt-0.5">{l}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="flex gap-2 flex-wrap">
        {SEVERITIES.map((s) => (
          <button
            key={s}
            onClick={() => setSeverity(s)}
            className={`text-xs px-3 py-1.5 rounded-full border transition-all ${
              severity === s
                ? "border-black dark:border-white text-black dark:text-white bg-gray-100 dark:bg-white/10 font-medium"
                : "border-gray-200 dark:border-[#272727] text-gray-500 dark:text-gray-500 hover:text-gray-800 dark:hover:text-gray-200 hover:border-gray-300 dark:hover:border-gray-600"
            }`}
          >
            {s === "" ? "All" : s.charAt(0).toUpperCase() + s.slice(1)}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="text-gray-400 dark:text-gray-600 text-sm">Loading...</div>
      ) : vulns.length === 0 ? (
        <div className="card p-8 text-center">
          <div className="text-gray-300 dark:text-gray-700 text-4xl mb-3">◎</div>
          <div className="text-gray-500 dark:text-gray-400 text-sm">No vulnerabilities found.</div>
          <div className="text-gray-400 dark:text-gray-600 text-xs mt-1">Click Ingest CVEs to fetch from NVD + OSV</div>
        </div>
      ) : (
        <div className="space-y-2">
          {vulns.map((v) => (
            <button
              key={v.id}
              onClick={() => navigate(`/vulnerabilities/${v.id}`)}
              className="card card-hover w-full text-left p-4 group"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="min-w-0 space-y-1.5">
                  <div className="flex items-center gap-3">
                    <span className="font-mono text-black dark:text-white text-sm font-semibold">{v.cve_id}</span>
                    {v.affected_packages.map((p, i) => (
                      <span key={i} className="text-xs bg-gray-100 dark:bg-[#1e1e1e] text-gray-500 dark:text-gray-400 px-2 py-0.5 rounded font-mono border border-gray-200 dark:border-[#333]">
                        {p.name}
                      </span>
                    ))}
                  </div>
                  <div className="text-gray-600 dark:text-gray-300 text-sm leading-snug line-clamp-2">{v.summary}</div>
                </div>
                <div className="shrink-0 flex flex-col items-end gap-1.5">
                  <SeverityBadge s={v.severity} />
                  {v.cvss_score != null && (
                    <span className="text-xs font-mono text-gray-400 dark:text-gray-500">CVSS {v.cvss_score}</span>
                  )}
                  <span className="text-xs text-gray-300 dark:text-gray-700 group-hover:text-black dark:group-hover:text-white transition-colors">→</span>
                </div>
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
