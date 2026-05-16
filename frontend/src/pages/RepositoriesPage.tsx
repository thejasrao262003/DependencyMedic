import { useEffect, useState } from "react";
import { api } from "../services/api";
import type { Repository } from "../types";

export default function RepositoriesPage() {
  const [repos, setRepos] = useState<Repository[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/repositories")
      .then((r) => setRepos(r.data.data ?? []))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="text-gray-400 dark:text-gray-600 text-sm">Loading...</div>;

  return (
    <div className="space-y-6 fade-up">
      <div>
        <h1 className="text-2xl font-semibold text-black dark:text-white">Repositories</h1>
        <p className="text-gray-500 dark:text-gray-400 text-sm mt-0.5">{repos.length} monitored</p>
      </div>

      {repos.length === 0 ? (
        <div className="card p-8 text-center">
          <div className="text-gray-300 dark:text-gray-700 text-4xl mb-3">⬡</div>
          <div className="text-gray-500 dark:text-gray-400 text-sm">No repositories found.</div>
          <div className="text-gray-400 dark:text-gray-600 text-xs mt-1 font-mono">make seed-demo</div>
        </div>
      ) : (
        <div className="space-y-3">
          {repos.map((repo) => (
            <div key={repo.id} className="card card-hover p-5">
              <div className="flex items-start justify-between gap-4">
                <div className="space-y-2 min-w-0">
                  <div className="flex items-center gap-3">
                    <span className="font-mono font-semibold text-black dark:text-white">{repo.repo_name}</span>
                    <span className={`w-1.5 h-1.5 rounded-full ${repo.status === "active" ? "bg-green-500 dot-pulse" : "bg-gray-300 dark:bg-gray-700"}`} />
                    <span className={`text-xs ${repo.status === "active" ? "text-green-600 dark:text-green-400 font-medium" : "text-gray-400 dark:text-gray-600"}`}>
                      {repo.status}
                    </span>
                  </div>
                  <a
                    href={repo.repo_url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-gray-400 dark:text-gray-600 text-xs hover:text-black dark:hover:text-white transition-colors truncate block underline underline-offset-2 hover:no-underline"
                    onClick={(e) => e.stopPropagation()}
                  >
                    {repo.repo_url}
                  </a>
                  <div className="flex gap-2 flex-wrap">
                    {repo.languages.map((lang) => (
                      <span key={lang} className="text-xs px-2 py-0.5 rounded-full font-medium bg-gray-100 dark:bg-[#1e1e1e] text-gray-600 dark:text-gray-400 border border-gray-200 dark:border-[#333]">
                        {lang}
                      </span>
                    ))}
                    {repo.tags.map((tag) => (
                      <span key={tag} className="text-xs px-2 py-0.5 rounded-full bg-gray-50 dark:bg-[#1a1a1a] text-gray-400 dark:text-gray-600 border border-gray-200 dark:border-[#272727]">
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="shrink-0 text-right space-y-1.5">
                  <div className="text-xs font-mono text-gray-400 dark:text-gray-600">#{repo.gitlab_project_id}</div>
                  <div className="text-xs text-gray-400 dark:text-gray-600">/{repo.default_branch}</div>
                  {repo.ci_enabled && (
                    <div className="text-xs text-green-600 dark:text-green-400 font-medium">CI ✓</div>
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
