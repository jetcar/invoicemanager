variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
}

variable "env_prefix" {
  description = "Prefix for secret names (e.g. invoicemanager-dev)"
  type        = string
}
