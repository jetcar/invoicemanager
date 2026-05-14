variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "apis" {
  description = "List of GCP APIs to enable"
  type        = list(string)
  default = [
    "container.googleapis.com",
    "artifactregistry.googleapis.com",
    "secretmanager.googleapis.com",
    "iam.googleapis.com",
    "iamcredentials.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "compute.googleapis.com",
    "sqladmin.googleapis.com",
    "servicenetworking.googleapis.com",
    "dns.googleapis.com",
    "logging.googleapis.com",
    "monitoring.googleapis.com",
    "sts.googleapis.com",
  ]
}
