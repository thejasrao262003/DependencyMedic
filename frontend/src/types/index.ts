export interface Vulnerability {
  id: string;
  cve_id: string;
  aliases: string[];
  summary: string;
  description: string;
  severity: "critical" | "high" | "medium" | "low" | "unknown";
  cvss_score: number | null;
  epss_score: number | null;
  published_at: string | null;
  affected_packages: AffectedPackage[];
  status: string;
  created_at: string;
  updated_at: string;
}

export interface AffectedPackage {
  name: string;
  ecosystem: string;
  affected_versions: string;
  fixed_versions: string[];
}

export interface Repository {
  id: string;
  repo_name: string;
  gitlab_project_id: string;
  default_branch: string;
  languages: string[];
  repo_url: string;
  ci_enabled: boolean;
  status: string;
  tags: string[];
  created_at: string;
  updated_at: string;
}

export interface PatchAttempt {
  id: string;
  repository_id: string;
  vulnerability_id: string;
  branch_name: string;
  dependency_changes: DependencyChange[];
  attempt_number: number;
  status: string;
  llm_used: boolean;
  confidence_score: number | null;
  retry_reason: string | null;
  patch_summary: string;
  created_at: string;
  updated_at: string;
}

export interface DependencyChange {
  package: string;
  from_version: string;
  to_version: string;
}

export interface PipelineRun {
  id: string;
  repository_id: string;
  patch_attempt_id: string;
  gitlab_pipeline_id: string;
  status: string;
  duration_seconds: number | null;
  failed_stage: string | null;
  failure_summary: string | null;
  logs_url: string | null;
  retry_attempted: boolean;
  created_at: string;
  updated_at: string;
}

export interface MergeRequest {
  id: string;
  repository_id: string;
  patch_attempt_id: string;
  gitlab_mr_id: string;
  title: string;
  status: string;
  reviewers: string[];
  approval_required: boolean;
  approved: boolean;
  mergeable: boolean;
  mr_url: string;
  created_at: string;
  updated_at: string;
}

export interface APIResponse<T> {
  success: boolean;
  data: T | null;
  error: { code: string; message: string } | null;
}
