output "pool_name" {
  description = "Full resource name of the Workload Identity Pool"
  value       = google_iam_workload_identity_pool.github.name
}

output "provider_name" {
  description = "Full resource name of the WIF OIDC provider"
  value       = google_iam_workload_identity_pool_provider.github.name
}

output "provider_id" {
  description = "Provider ID (short form) used in GitHub Actions google-github-actions/auth"
  value       = google_iam_workload_identity_pool_provider.github.name
}
