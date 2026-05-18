# prod environment — project_id is supplied by CI via TF_VAR_project_id or set locally before apply
# For local usage, copy this file and replace the placeholder with your real project ID.
region            = "europe-west1"
github_repository = "jetcar/invoicemanager"

master_authorized_networks = [
  {
    cidr_block   = "0.0.0.0/0"   # Replace with your office/VPN CIDR
    display_name = "all"
  }
]
