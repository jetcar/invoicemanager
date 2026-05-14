project_id        = "invoicemanager-prod-CHANGEME"
region            = "europe-west1"
github_repository = "jetcar/invoicemanager"

master_authorized_networks = [
  {
    cidr_block   = "0.0.0.0/0"   # Replace with your office/VPN CIDR
    display_name = "all"
  }
]
