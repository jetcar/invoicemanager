variable "project_id" {
  description = "GCP project ID for the dev environment"
  type        = string
}

variable "region" {
  description = "Primary GCP region"
  type        = string
  default     = "europe-west1"
}

variable "github_repository" {
  description = "GitHub repository in owner/repo format"
  type        = string
  default     = "jetcar/invoicemanager"
}
