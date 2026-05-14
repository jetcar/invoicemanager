locals {
  # Secondary IP ranges required by GKE Autopilot (pods + services)
  pod_range     = "${var.name}-pods"
  service_range = "${var.name}-services"
}

resource "google_compute_network" "vpc" {
  name                    = var.name
  project                 = var.project_id
  auto_create_subnetworks = false
  routing_mode            = "REGIONAL"
}

resource "google_compute_subnetwork" "gke" {
  name                     = "${var.name}-gke"
  project                  = var.project_id
  region                   = var.region
  network                  = google_compute_network.vpc.self_link
  ip_cidr_range            = var.subnet_cidr
  private_ip_google_access = true

  secondary_ip_range {
    range_name    = local.pod_range
    ip_cidr_range = var.pods_cidr
  }

  secondary_ip_range {
    range_name    = local.service_range
    ip_cidr_range = var.services_cidr
  }

  log_config {
    aggregation_interval = "INTERVAL_10_MIN"
    flow_sampling        = 0.5
    metadata             = "INCLUDE_ALL_METADATA"
  }
}

resource "google_compute_router" "router" {
  name    = "${var.name}-router"
  project = var.project_id
  region  = var.region
  network = google_compute_network.vpc.self_link
}

resource "google_compute_router_nat" "nat" {
  name                               = "${var.name}-nat"
  project                            = var.project_id
  router                             = google_compute_router.router.name
  region                             = var.region
  nat_ip_allocate_option             = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"

  log_config {
    enable = true
    filter = "ERRORS_ONLY"
  }
}

# Allow internal communication within the VPC
resource "google_compute_firewall" "allow_internal" {
  name    = "${var.name}-allow-internal"
  project = var.project_id
  network = google_compute_network.vpc.self_link

  allow {
    protocol = "tcp"
  }
  allow {
    protocol = "udp"
  }
  allow {
    protocol = "icmp"
  }

  source_ranges = [var.subnet_cidr, var.pods_cidr, var.services_cidr]
  priority      = 1000
}

# Allow health checks from GCP load balancers
resource "google_compute_firewall" "allow_health_check" {
  name    = "${var.name}-allow-health-check"
  project = var.project_id
  network = google_compute_network.vpc.self_link

  allow {
    protocol = "tcp"
  }

  source_ranges = ["35.191.0.0/16", "130.211.0.0/22"]
  priority      = 1000
}
