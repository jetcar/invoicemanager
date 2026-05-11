variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "github_repository" {
  description = "GitHub repository in 'owner/repo' format (e.g. jetcar/invoicemanager)"
  type        = string
}

variable "github_actions_sa_emails" {
  description = "Map of environment name → GitHub Actions service account email to bind to WIF"
  type        = map(string)
  # Example: { dev = "github-actions-dev@project.iam.gserviceaccount.com" }
}
