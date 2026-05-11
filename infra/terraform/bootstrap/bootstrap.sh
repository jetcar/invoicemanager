#!/usr/bin/env bash
# bootstrap.sh
#
# One-time manual bootstrap script.
# Run this ONCE from a GCP account with Owner/Editor access to create:
#   1. GCS buckets for Terraform state per environment
#   2. The bootstrap Terraform plan is then applied with the GitHub Actions SA
#      credentials obtained via Workload Identity Federation.
#
# After this script you should never need to touch the GCP Console again.
#
# Usage:
#   export GCP_PROJECT_DEV=my-dev-project
#   export GCP_PROJECT_STAGING=my-staging-project
#   export GCP_PROJECT_PROD=my-prod-project
#   export GITHUB_REPO=jetcar/invoicemanager
#   ./bootstrap.sh

set -euo pipefail

: "${GCP_PROJECT_DEV:?Set GCP_PROJECT_DEV}"
: "${GCP_PROJECT_STAGING:?Set GCP_PROJECT_STAGING}"
: "${GCP_PROJECT_PROD:?Set GCP_PROJECT_PROD}"
: "${GITHUB_REPO:?Set GITHUB_REPO (owner/repo)}"

REGION="${REGION:-europe-west1}"

create_tfstate_bucket() {
  local project="$1"
  local env="$2"
  local bucket="invoicemanager-tfstate-${env}"

  echo "→ Creating Terraform state bucket: gs://${bucket}"
  gcloud storage buckets create "gs://${bucket}" \
    --project="${project}" \
    --location="${REGION}" \
    --uniform-bucket-level-access \
    --public-access-prevention || echo "  (bucket already exists — skipping)"

  # Enable versioning for state file safety
  gcloud storage buckets update "gs://${bucket}" --versioning
}

enable_apis() {
  local project="$1"
  echo "→ Enabling bootstrap APIs on ${project}"
  gcloud services enable \
    cloudresourcemanager.googleapis.com \
    iam.googleapis.com \
    iamcredentials.googleapis.com \
    sts.googleapis.com \
    storage.googleapis.com \
    --project="${project}"
}

echo "═══════════════════════════════════════════════"
echo " InvoiceManager GCP Bootstrap"
echo " Repo: ${GITHUB_REPO}"
echo "═══════════════════════════════════════════════"

for env_pair in "dev:${GCP_PROJECT_DEV}" "staging:${GCP_PROJECT_STAGING}" "prod:${GCP_PROJECT_PROD}"; do
  env="${env_pair%%:*}"
  project="${env_pair##*:}"

  echo ""
  echo "── Environment: ${env} (project: ${project}) ──"
  enable_apis "${project}"
  create_tfstate_bucket "${project}" "${env}"

  echo "→ Updating terraform.tfvars for ${env}"
  sed -i "s/invoicemanager-${env}-CHANGEME/${project}/" \
    "../environments/${env}/terraform.tfvars" || true
done

echo ""
echo "✓ Bootstrap complete!"
echo ""
echo "Next steps:"
echo "  1. cd ../environments/dev && terraform init && terraform apply"
echo "  2. Copy the 'wif_provider' and 'github_actions_sa_email' outputs"
echo "  3. Add these as GitHub repository secrets:"
echo "       GCP_WIF_PROVIDER_DEV     = <wif_provider output>"
echo "       GCP_SA_EMAIL_DEV         = <github_actions_sa_email output>"
echo "       GCP_PROJECT_ID_DEV       = ${GCP_PROJECT_DEV}"
echo "       GCP_REGION               = ${REGION}"
echo "     (repeat for staging/prod)"
echo "  4. Set real secret values in GCP Secret Manager (see docs/gcp-setup.md)"
