import { useEffect, useState } from "react";
import { api } from "../services/api";
import type { Repository } from "../types";

const LANG_COLOR: Record<string, string> = {
  java: "bg-orange-900/40 text-orange-300",
  python: "bg-blue-900/40 text-blue-300",
  javascript: "bg-yellow-900/40 text-yellow-300",
  typescript: "bg-blue-900/40 text-blue-300",
  go: "bg-cyan-900/40 text-cyan-300",
};

const STATUS_COLOR: Record<string, string> = {
  active: "text-green-400",
  scanning: "text-yellow-400",
  inactive: "text-gray-500",
};

export default function RepositoriesPage() {
  const [repos, setRepos] = useState<Repository[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get("/repositories")
      .then((r) => setRepos(r.data.data ?? []))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="text-gray-400">Loading...</div>;

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-bold">Repositories</h1>
      {repos.length === 0 ? (
        <div className="text-gray-500 text-sm">
          No repositories found. Run <code className="text-blue-400">make seed-demo</code> to load demo data.
        </div>
      ) : (
        <div className="space-y-3">
          {repos.map((repo) => (
            <div key={repo.id} className="bg-gray-900 border border-gray-800 rounded-lg p-4">
              <div className="flex items-start justify-between">
                <div className="space-y-1">
                  <div className="flex items-center gap-3">
                    <span className="font-mono text-white font-medium">{repo.repo_name}</span>
                    <span className={`text-xs font-medium ${STATUS_COLOR[repo.status] ?? "text-gray-400"}`}>
                      ● {repo.status}
                    </span>
                  </div>
                  <a
                    href={repo.repo_url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-blue-400 text-xs hover:underline"
                  >
                    {repo.repo_url}
                  </a>
                  <div className="flex gap-2 mt-2 flex-wrap">
                    {repo.languages.map((lang) => (
                      <span
                        key={lang}
                        className={`text-xs px-2 py-0.5 rounded ${LANG_COLOR[lang] ?? "bg-gray-800 text-gray-300"}`}
                      >
                        {lang}
                      </span>
                    ))}
                    {repo.tags.map((tag) => (
                      <span key={tag} className="text-xs px-2 py-0.5 rounded bg-gray-800 text-gray-400">
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
                <div className="text-right text-xs text-gray-500 space-y-1">
                  <div>ID: {repo.gitlab_project_id}</div>
                  <div>Branch: {repo.default_branch}</div>
                  {repo.ci_enabled && (
                    <div className="text-green-500">CI enabled</div>
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
