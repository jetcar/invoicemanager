output "secret_ids" {
  description = "Map of logical name → Secret Manager resource ID"
  value       = { for k, v in google_secret_manager_secret.secrets : k => v.secret_id }
}

output "secret_names" {
  description = "Map of logical name → Secret Manager secret name (for ESO references)"
  value       = local.secret_names
}
