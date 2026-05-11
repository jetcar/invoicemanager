output "github_actions_sa_email" {
  description = "GitHub Actions service account email"
  value       = google_service_account.github_actions.email
}

output "github_actions_sa_name" {
  description = "GitHub Actions service account resource name"
  value       = google_service_account.github_actions.name
}

output "gke_node_sa_email" {
  description = "GKE node service account email"
  value       = google_service_account.gke_node.email
}

output "app_sa_email" {
  description = "InvoiceManager application service account email"
  value       = google_service_account.app.email
}
