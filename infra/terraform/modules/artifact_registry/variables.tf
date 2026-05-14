variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "location" {
  description = "Artifact Registry location (region)"
  type        = string
}

variable "repository_id" {
  description = "Artifact Registry repository ID"
  type        = string
  default     = "invoicemanager"
}

variable "keep_tag_count" {
  description = "Number of most-recent tagged versions to retain per image"
  type        = number
  default     = 10
}

variable "delete_older_than_days" {
  description = "Delete untagged images older than this many days"
  type        = number
  default     = 30
}
