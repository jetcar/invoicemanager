# ──────────────────────────────────────────────
# GitHub Actions service account
# ──────────────────────────────────────────────
resource "google_service_account" "github_actions" {
  project      = var.project_id
  account_id   = "github-actions-${var.environment}"
  display_name = "GitHub Actions CI/CD (${var.environment})"
  description  = "Used by GitHub Actions via Workload Identity Federation to manage ${var.environment} infra and deployments"
}

# Allow GitHub Actions SA to push images to Artifact Registry
resource "google_project_iam_member" "github_artifact_writer" {
  project = var.project_id
  role    = "roles/artifactregistry.writer"
  member  = "serviceAccount:${google_service_account.github_actions.email}"
}

# Allow GitHub Actions SA to deploy to GKE
resource "google_project_iam_member" "github_gke_developer" {
  project = var.project_id
  role    = "roles/container.developer"
  member  = "serviceAccount:${google_service_account.github_actions.email}"
}

# Allow GitHub Actions SA to run Terraform (storage, compute reads, etc.)
resource "google_project_iam_member" "github_terraform_state" {
  project = var.project_id
  role    = "roles/storage.admin"
  member  = "serviceAccount:${google_service_account.github_actions.email}"
}

resource "google_project_iam_member" "github_editor" {
  project = var.project_id
  role    = "roles/editor"
  member  = "serviceAccount:${google_service_account.github_actions.email}"
}

# Needed for Terraform to manage IAM policies
resource "google_project_iam_member" "github_iam_admin" {
  project = var.project_id
  role    = "roles/resourcemanager.projectIamAdmin"
  member  = "serviceAccount:${google_service_account.github_actions.email}"
}

# ──────────────────────────────────────────────
# GKE node service account
# ──────────────────────────────────────────────
resource "google_service_account" "gke_node" {
  project      = var.project_id
  account_id   = "gke-node-${var.environment}"
  display_name = "GKE Node SA (${var.environment})"
  description  = "Service account for GKE nodes in ${var.environment}"
}

resource "google_project_iam_member" "gke_node_log_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.gke_node.email}"
}

resource "google_project_iam_member" "gke_node_metric_writer" {
  project = var.project_id
  role    = "roles/monitoring.metricWriter"
  member  = "serviceAccount:${google_service_account.gke_node.email}"
}

resource "google_project_iam_member" "gke_node_monitoring_viewer" {
  project = var.project_id
  role    = "roles/monitoring.viewer"
  member  = "serviceAccount:${google_service_account.gke_node.email}"
}

resource "google_project_iam_member" "gke_node_artifact_reader" {
  project = var.project_id
  role    = "roles/artifactregistry.reader"
  member  = "serviceAccount:${google_service_account.gke_node.email}"
}

# Allow GKE nodes to access Secret Manager secrets
resource "google_project_iam_member" "gke_node_secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.gke_node.email}"
}

# ──────────────────────────────────────────────
# Application service account (for in-pod WI)
# ──────────────────────────────────────────────
resource "google_service_account" "app" {
  project      = var.project_id
  account_id   = "invoicemanager-app-${var.environment}"
  display_name = "InvoiceManager App SA (${var.environment})"
  description  = "Used by InvoiceManager pods via Workload Identity to access GCP services"
}

resource "google_project_iam_member" "app_secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.app.email}"
}

# Allow KSA (Kubernetes Service Account) to impersonate the GCP SA via WI
resource "google_service_account_iam_member" "app_workload_identity" {
  service_account_id = google_service_account.app.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "serviceAccount:${var.project_id}.svc.id.goog[invoicemanager/invoicemanager-app]"
}
