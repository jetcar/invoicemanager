terraform {
  required_version = ">= 1.9"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 6.0"
    }
  }

  backend "gcs" {
    bucket = "invoicemanager-tfstate-dev"
    prefix = "terraform/state"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
}

# ── Enable APIs ──────────────────────────────────────────────────────────────
module "apis" {
  source     = "../../modules/apis"
  project_id = var.project_id
}

# ── Networking ───────────────────────────────────────────────────────────────
module "network" {
  source     = "../../modules/network"
  project_id = var.project_id
  name       = "invoicemanager-dev"
  region     = var.region

  depends_on = [module.apis]
}

# ── GKE Autopilot ────────────────────────────────────────────────────────────
module "gke" {
  source = "../../modules/gke"

  project_id         = var.project_id
  cluster_name       = "invoicemanager-dev"
  region             = var.region
  network            = module.network.network_name
  subnetwork         = module.network.subnet_name
  pod_range_name     = module.network.pod_range_name
  service_range_name = module.network.service_range_name

  deletion_protection = false
  release_channel     = "REGULAR"

  depends_on = [module.apis, module.network]
}

# ── Artifact Registry ─────────────────────────────────────────────────────────
module "artifact_registry" {
  source     = "../../modules/artifact_registry"
  project_id = var.project_id
  location   = var.region

  depends_on = [module.apis]
}

# ── IAM ──────────────────────────────────────────────────────────────────────
module "iam" {
  source      = "../../modules/iam"
  project_id  = var.project_id
  environment = "dev"

  depends_on = [module.apis, module.gke]
}

# ── Secret Manager ────────────────────────────────────────────────────────────
module "secrets" {
  source      = "../../modules/secret_manager"
  project_id  = var.project_id
  environment = "dev"
  env_prefix  = "invoicemanager-dev"

  depends_on = [module.apis]
}

# ── Workload Identity Federation ──────────────────────────────────────────────
module "workload_identity" {
  source     = "../../modules/workload_identity"
  project_id = var.project_id

  github_repository = var.github_repository

  github_actions_sa_emails = {
    dev = module.iam.github_actions_sa_email
  }

  depends_on = [module.iam]
}
