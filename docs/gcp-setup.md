# GCP Integration Setup Guide

This document is the **single source of truth** for setting up GitHub → GCP integration for InvoiceManager. After completing this guide, all infrastructure changes and deployments happen exclusively through GitHub — no manual GCP Console operations are needed.

---

## Architecture Overview

```
GitHub (main branch)
│
├── .github/workflows/
│   ├── test.yml            ← runs unit tests on every PR
│   ├── infra-plan.yml      ← terraform plan on every PR touching infra/
│   ├── infra-apply.yml     ← terraform apply on merge to main
│   ├── build-deploy.yml    ← build images, push to GAR, helm deploy
│   └── drift-detection.yml ← daily scheduled terraform plan
│
infra/terraform/
│   ├── modules/            ← reusable Terraform modules
│   └── environments/
│       ├── dev/            ← dev GCP project
│       ├── staging/        ← staging GCP project
│       └── prod/           ← prod GCP project
│
k8s/helm/invoicemanager/    ← Helm chart (all 7 services + infra)
```

### GCP Components per Environment

| Component | Resource |
|---|---|
| Compute | GKE Autopilot cluster |
| Images | Artifact Registry (Docker) |
| Secrets | Secret Manager |
| Networking | VPC + private subnet + Cloud NAT |
| Auth | Workload Identity Federation (no static keys) |
| State | GCS bucket per environment |

---

## Prerequisites

- GCP account with billing enabled
- Three GCP projects (or reuse one for dev/staging, separate for prod)
- `gcloud` CLI installed and authenticated (`gcloud auth login`)
- `terraform` ≥ 1.9 installed
- `helm` ≥ 3.16 installed
- GitHub repository admin access (to configure Environments and Secrets)

---

## Step 1: Bootstrap GCP Projects (One-Time Manual Step)

This is the **only step that requires the GCP Console or `gcloud` CLI**. Everything after this is automated.

```bash
cd infra/terraform/bootstrap

export GCP_PROJECT_DEV=my-invoicemanager-dev       # your real project IDs
export GCP_PROJECT_STAGING=my-invoicemanager-staging
export GCP_PROJECT_PROD=my-invoicemanager-prod
export GITHUB_REPO=jetcar/invoicemanager
export REGION=europe-west1

./bootstrap.sh
```

This script:
1. Enables the minimum required GCP APIs on each project
2. Creates GCS buckets for Terraform state (`invoicemanager-tfstate-{dev,staging,prod}`)
3. Patches the `terraform.tfvars` files with your real project IDs

---

## Step 2: Apply Terraform for the First Time

Run once per environment to provision all GCP resources:

```bash
# Dev
cd infra/terraform/environments/dev
terraform init
terraform apply

# Note the outputs:
#   wif_provider            → used as GCP_WIF_PROVIDER_DEV
#   github_actions_sa_email → used as GCP_SA_EMAIL_DEV
#   artifact_registry_url   → used as GCP_REGISTRY_DEV
```

Repeat for `staging` and `prod`.

---

## Step 3: Configure GitHub Repository Secrets

Go to **GitHub → Settings → Secrets and variables → Actions** and add:

### Per-environment secrets

| Secret | Value | Where to find |
|---|---|---|
| `GCP_WIF_PROVIDER_DEV` | WIF provider name | `terraform output wif_provider` in dev |
| `GCP_SA_EMAIL_DEV` | GitHub Actions SA email | `terraform output github_actions_sa_email` in dev |
| `GCP_PROJECT_ID_DEV` | GCP project ID | your dev project ID |
| `GCP_REGISTRY_DEV` | Artifact Registry URL | `terraform output artifact_registry_url` in dev |
| `GCP_APP_SA_EMAIL_DEV` | App SA email | `terraform output` → IAM module app SA |
| `GCP_WIF_PROVIDER_STAGING` | WIF provider name | same for staging |
| `GCP_SA_EMAIL_STAGING` | GitHub Actions SA email | same for staging |
| `GCP_PROJECT_ID_STAGING` | GCP project ID | your staging project ID |
| `GCP_REGISTRY_STAGING` | Artifact Registry URL | same for staging |
| `GCP_APP_SA_EMAIL_STAGING` | App SA email | same for staging |
| `GCP_WIF_PROVIDER_PROD` | WIF provider name | same for prod |
| `GCP_SA_EMAIL_PROD` | GitHub Actions SA email | same for prod |
| `GCP_PROJECT_ID_PROD` | GCP project ID | your prod project ID |
| `GCP_REGISTRY_PROD` | Artifact Registry URL | same for prod |
| `GCP_APP_SA_EMAIL_PROD` | App SA email | same for prod |

### Shared secrets

| Secret | Value |
|---|---|
| `GCP_REGION` | `europe-west1` (or your chosen region) |

---

## Step 4: Configure GitHub Environments

Go to **GitHub → Settings → Environments** and create:

| Environment | Protection rules |
|---|---|
| `dev` | None (auto-deploy) |
| `staging` | Optional: wait timer (e.g., 5 min) |
| `production` | Required reviewers: add at least 1 person |

Each environment uses its own set of secrets (set per-environment secrets in the Environment settings, not repo-level, for better isolation).

---

## Step 5: Set Real Secret Values in GCP Secret Manager

Terraform created placeholder secret versions. Replace them with real values before the first deployment:

```bash
# Replace ENVIRONMENT with dev, staging, or prod
ENVIRONMENT=dev
PROJECT=my-invoicemanager-dev

# PostgreSQL password
echo -n "my-strong-postgres-password" | \
  gcloud secrets versions add "invoicemanager-${ENVIRONMENT}-postgres-password" \
    --project="${PROJECT}" --data-file=-

# Redis password
echo -n "my-strong-redis-password" | \
  gcloud secrets versions add "invoicemanager-${ENVIRONMENT}-redis-password" \
    --project="${PROJECT}" --data-file=-

# JWT secret key (generate with: openssl rand -hex 32)
openssl rand -hex 32 | \
  gcloud secrets versions add "invoicemanager-${ENVIRONMENT}-secret-key" \
    --project="${PROJECT}" --data-file=-

# SMTP credentials
echo -n "smtp-username@example.com" | \
  gcloud secrets versions add "invoicemanager-${ENVIRONMENT}-smtp-user" \
    --project="${PROJECT}" --data-file=-

echo -n "smtp-password" | \
  gcloud secrets versions add "invoicemanager-${ENVIRONMENT}-smtp-password" \
    --project="${PROJECT}" --data-file=-

# Firebase credentials (paste the full JSON content)
cat /path/to/firebase-credentials.json | \
  gcloud secrets versions add "invoicemanager-${ENVIRONMENT}-firebase-credentials-json" \
    --project="${PROJECT}" --data-file=-
```

---

## Step 6: Install External Secrets Operator in GKE

The Helm chart uses [External Secrets Operator](https://external-secrets.io/) to sync GCP Secret Manager → Kubernetes Secrets.

```bash
# Get cluster credentials
gcloud container clusters get-credentials invoicemanager-dev \
  --region=europe-west1 --project=my-invoicemanager-dev

# Install ESO via Helm
helm repo add external-secrets https://charts.external-secrets.io
helm repo update
helm install external-secrets external-secrets/external-secrets \
  --namespace external-secrets \
  --create-namespace \
  --set installCRDs=true \
  --wait
```

> After the first `build-deploy.yml` run, all subsequent ESO installs/upgrades are handled automatically by the pipeline. This one-time install only needs to happen once per cluster.

---

## Step 7: First Deployment

Push a commit to `main` (or trigger `build-deploy.yml` manually):

```
GitHub push → build-deploy.yml:
  build job   → builds 7 Docker images, pushes to Artifact Registry
  deploy-dev  → helm upgrade invoicemanager in GKE dev
  (approval)
  deploy-staging → helm upgrade in GKE staging
  (approval from required reviewer)
  deploy-prod → helm upgrade in GKE production
```

---

## Day-to-Day Workflows

### Deploy a code change
1. Create a branch, make your change, open a PR.
2. `test.yml` runs unit tests automatically.
3. Merge to `main` → `build-deploy.yml` builds and promotes through dev → staging → prod.

### Change infrastructure
1. Edit files under `infra/terraform/`.
2. Open a PR → `infra-plan.yml` posts a Terraform plan as a PR comment.
3. Review the plan, merge → `infra-apply.yml` applies the change through dev → staging → prod.

### Rollback a deployment
```bash
# List Helm release history
helm history invoicemanager -n invoicemanager

# Roll back to the previous revision
helm rollback invoicemanager -n invoicemanager

# Or roll back to a specific image tag via workflow_dispatch:
# Go to Actions → Build and Deploy → Run workflow
# Enter the image_tag of the known-good commit SHA
```

### Rollback infrastructure
```bash
# Revert the Terraform change in Git and push to main.
# The infra-apply.yml pipeline will restore the previous state.

# For emergency: run terraform apply from local with the previous commit
git checkout <previous-commit> -- infra/terraform/environments/prod/
cd infra/terraform/environments/prod
terraform apply
```

---

## Migrating to Managed GCP Services (Optional)

The initial setup uses in-cluster PostgreSQL, Redis, and Kafka (StatefulSets). When you're ready to migrate to fully managed services:

| Current | Managed replacement | Terraform module to add |
|---|---|---|
| In-cluster Postgres | Cloud SQL for PostgreSQL | Add `modules/cloud_sql` |
| In-cluster Redis | Memorystore for Redis | Add `modules/memorystore` |
| In-cluster Kafka | Cloud Pub/Sub | Application code change needed |

To switch, set `infrastructure.postgres.enabled: false` (etc.) in the Helm values file for the target environment, and update the `DATABASE_URL` env vars to point at the managed service endpoint.

---

## Security Notes

- **No static service account keys** are ever stored in GitHub Secrets or the codebase. All authentication uses short-lived OIDC tokens via Workload Identity Federation.
- Secrets live only in GCP Secret Manager and are never committed to Git.
- The `invoicemanager-secrets` Kubernetes Secret is owned by External Secrets Operator and auto-refreshed every hour.
- GKE nodes use a minimal-privilege service account (no `compute.admin`, no `storage.objectAdmin`).
- Production GKE cluster uses `STABLE` release channel and has deletion protection enabled.
- Branch protection + required CI checks should be enforced on `main` (set in GitHub → Settings → Branches).
