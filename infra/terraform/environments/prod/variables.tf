variable "project_id" {
  description = "GCP project ID for the production environment"
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

variable "master_authorized_networks" {
  description = "Authorized networks for GKE control-plane access in production"
  type = list(object({
    cidr_block   = string
    display_name = string
  }))
  # Restrict to your office / VPN IPs in production
  default = [
    {
      cidr_block   = "0.0.0.0/0"
      display_name = "all (tighten this before go-live)"
    }
  ]
}
