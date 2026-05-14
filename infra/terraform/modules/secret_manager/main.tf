locals {
  # All secrets needed by InvoiceManager services.
  # Values are set to placeholder strings - actual values must be populated
  # via: gcloud secrets versions add <name> --data-file=-
  # or via the GCP Console on first deploy.
  secret_names = {
    postgres_user            = "${var.env_prefix}-postgres-user"
    postgres_password        = "${var.env_prefix}-postgres-password"
    redis_password           = "${var.env_prefix}-redis-password"
    secret_key               = "${var.env_prefix}-secret-key"
    smtp_user                = "${var.env_prefix}-smtp-user"
    smtp_password            = "${var.env_prefix}-smtp-password"
    firebase_credentials     = "${var.env_prefix}-firebase-credentials-json"
  }
}

resource "google_secret_manager_secret" "secrets" {
  for_each  = local.secret_names
  project   = var.project_id
  secret_id = each.value

  replication {
    auto {}
  }

  labels = {
    environment = var.environment
    managed-by  = "terraform"
  }
}

# Placeholder initial versions (value must be replaced before first deploy)
resource "google_secret_manager_secret_version" "placeholders" {
  for_each = local.secret_names

  secret      = google_secret_manager_secret.secrets[each.key].id
  secret_data = "PLACEHOLDER_${upper(each.key)}_CHANGE_BEFORE_DEPLOY"

  lifecycle {
    # Never overwrite a secret version once it has been manually set
    ignore_changes = [secret_data]
  }
}
