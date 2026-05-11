resource "google_artifact_registry_repository" "images" {
  project       = var.project_id
  location      = var.location
  repository_id = var.repository_id
  description   = "InvoiceManager container images"
  format        = "DOCKER"

  cleanup_policy_dry_run = false

  cleanup_policies {
    id     = "keep-last-10"
    action = "KEEP"

    most_recent_versions {
      keep_count = var.keep_tag_count
    }
  }

  cleanup_policies {
    id     = "delete-old"
    action = "DELETE"

    condition {
      older_than = "${var.delete_older_than_days * 24}h" # days → hours (Artifact Registry uses duration strings)
      tag_state  = "UNTAGGED"
    }
  }
}
