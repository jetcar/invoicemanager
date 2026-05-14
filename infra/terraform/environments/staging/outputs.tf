output "cluster_name" {
  value = module.gke.cluster_name
}

output "artifact_registry_url" {
  value = module.artifact_registry.repository_url
}

output "github_actions_sa_email" {
  value = module.iam.github_actions_sa_email
}

output "wif_provider" {
  value = module.workload_identity.provider_name
}

output "secret_names" {
  value = module.secrets.secret_names
}
