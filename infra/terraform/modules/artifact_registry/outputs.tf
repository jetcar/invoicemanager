output "repository_id" {
  description = "Artifact Registry repository ID"
  value       = google_artifact_registry_repository.images.repository_id
}

output "repository_url" {
  description = "Full URL prefix for pushing/pulling images"
  value       = "${var.location}-docker.pkg.dev/${var.project_id}/${var.repository_id}"
}
