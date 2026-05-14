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
    bucket = "invoicemanager-tfstate-prod"
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

module "apis" {
  source     = "../../modules/apis"
  project_id = var.project_id
}

module "network" {
  source     = "../../modules/network"
  project_id = var.project_id
  name       = "invoicemanager-prod"
  region     = var.region

  # Larger ranges for production scale
  subnet_cidr   = "10.100.0.0/20"
  pods_cidr     = "10.200.0.0/16"
  services_cidr = "10.210.0.0/20"

  depends_on = [module.apis]
}

module "gke" {
  source = "../../modules/gke"

  project_id         = var.project_id
  cluster_name       = "invoicemanager-prod"
  region             = var.region
  network            = module.network.network_name
  subnetwork         = module.network.subnet_name
  pod_range_name     = module.network.pod_range_name
  service_range_name = module.network.service_range_name

  deletion_protection = true
  release_channel     = "STABLE"

  # Restrict control-plane access to known IPs in production
  master_authorized_networks = var.master_authorized_networks

  depends_on = [module.apis, module.network]
}

module "artifact_registry" {
  source     = "../../modules/artifact_registry"
  project_id = var.project_id
  location   = var.region

  # Keep more versions in prod
  keep_tag_count         = 20
  delete_older_than_days = 90

  depends_on = [module.apis]
}

module "iam" {
  source      = "../../modules/iam"
  project_id  = var.project_id
  environment = "prod"

  depends_on = [module.apis]
}

module "secrets" {
  source      = "../../modules/secret_manager"
  project_id  = var.project_id
  environment = "prod"
  env_prefix  = "invoicemanager-prod"

  depends_on = [module.apis]
}

module "workload_identity" {
  source     = "../../modules/workload_identity"
  project_id = var.project_id

  github_repository = var.github_repository

  github_actions_sa_emails = {
    prod = module.iam.github_actions_sa_email
  }

  depends_on = [module.iam]
}
