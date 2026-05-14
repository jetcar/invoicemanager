output "enabled_apis" {
  description = "Map of enabled API services"
  value       = { for k, v in google_project_service.apis : k => v.service }
}
