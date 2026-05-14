# GCP Integration Setup Guide

This document is the **single source of truth** for setting up GitHub → GCP integration for InvoiceManager. After completing this guide, all infrastructure changes and deployments happen exclusively through GitHub — no manual GCP Console operations are needed.

---

## Architecture Overview

```
GitHub (main branch)
│
├── .github/workflows/
│   ├── test.yml              ← runs unit tests on every PR
│   ├── infra-plan.yml        ← terraform plan on every PR touching infra/
│   ├── infra-apply.yml       ← terraform apply on merge to main (requires WIF)
│   ├── infra-bootstrap.yml   ← one-time initial dev provisioning (uses SA key)
│   ├── build-deploy.yml      ← build images, push to GAR, helm deploy
│   └── drift-detection.yml   ← daily scheduled terraform plan
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

### Bootstrap vs Ongoing workflows

| Workflow | When to use | Auth method | Trigger |
|---|---|---|---|
| `infra-bootstrap.yml` | **First-time** dev setup only; cluster does not exist yet | SA JSON key (`GCP_SA_KEY_DEV`) | Manual `workflow_dispatch` |
| `infra-apply.yml` | All subsequent infra changes | Workload Identity Federation (WIF) | Push to `main` / manual |
| `build-deploy.yml` | App deployments after infra exists | WIF | Push to `main` / manual |

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

## Step 1: Bootstrap Dev Environment via GitHub Actions (Recommended)

The `infra-bootstrap.yml` workflow replaces the previously manual Step 1 + Step 2 for the dev environment. It requires only **two secrets** to be added once to your GitHub repository:

### 1a. Create a short-lived bootstrap service account key

In GCP Console → IAM → Service Accounts, create (or use an existing) service account with **Owner** or **Editor** role on your dev project. Then:

1. Click the service account → **Keys** tab → **Add Key** → **JSON**.
2. Download the JSON file.

> This key is used **only for the initial bootstrap run**. Once WIF is set up you should delete this key.

### 1b. Add the two bootstrap secrets to GitHub

Go to **GitHub → Settings → Secrets and variables → Actions** and add:

| Secret | Value |
|---|---|
| `GCP_SA_KEY_DEV` | Full contents of the JSON key file downloaded above |
| `GCP_PROJECT_ID_DEV` | Your dev GCP project ID (e.g. `invoicemanager-496308`) |

### 1c. Run the bootstrap workflow

1. Go to **GitHub → Actions → Infra Bootstrap (Dev — Initial Setup)**.
2. Click **Run workflow**.
3. Type `bootstrap-dev` in the confirmation field.
4. Click **Run workflow**.

The workflow will:
1. Enable all required GCP APIs on the dev project.
2. Create the Terraform state bucket (`invoicemanager-tfstate-dev`).
3. Run `terraform init` + `terraform apply` to provision the full dev environment (GKE, Artifact Registry, IAM, WIF, Secret Manager, networking).
4. Print the Terraform outputs you need for the next step.

### 1d. Capture Terraform outputs

When the workflow finishes, open the **"Bootstrap outputs"** step in the Actions log and copy the values printed there:

```
GCP_WIF_PROVIDER_DEV  = projects/.../locations/global/workloadIdentityPools/...
GCP_SA_EMAIL_DEV      = github-actions-dev@<project>.iam.gserviceaccount.com
GCP_REGISTRY_DEV      = europe-west1-docker.pkg.dev/<project>/invoicemanager
GCP_APP_SA_EMAIL_DEV  = invoicemanager-app-dev@<project>.iam.gserviceaccount.com
```

---

## Step 1 (Alternative): Manual Bootstrap with Local `gcloud`

If you prefer a fully local bootstrap (or need to bootstrap staging/prod), you can run the script directly:

```bash
cd infra/terraform/bootstrap

export GCP_PROJECT_DEV=my-invoicemanager-dev       # your real project IDs
export GCP_PROJECT_STAGING=my-invoicemanager-staging
export GCP_PROJECT_PROD=my-invoicemanager-prod
export GITHUB_REPO=jetcar/invoicemanager
export REGION=europe-west1

./bootstrap.sh
```

Then run Terraform manually:

```bash
cd infra/terraform/environments/dev
terraform init
terraform apply
```

---

## Step 2: Configure GitHub Repository Secrets (after bootstrap)

After either bootstrap path, add these secrets so that `infra-apply.yml` and `build-deploy.yml` can use Workload Identity Federation.

> **If you used the GitHub Actions bootstrap workflow**, copy the values from the "Bootstrap outputs" step in the Actions log.

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

## Step 3: Configure GitHub Environments

Go to **GitHub → Settings → Environments** and create:

| Environment | Protection rules |
|---|---|
| `dev` | None (auto-deploy) |
| `staging` | Optional: wait timer (e.g., 5 min) |
| `production` | Required reviewers: add at least 1 person |

Each environment uses its own set of secrets (set per-environment secrets in the Environment settings, not repo-level, for better isolation).

---

## Step 4: Set Real Secret Values in GCP Secret Manager

Terraform created placeholder secret versions. Replace them with real values before the first deployment:

```bash
# Replace ENVIRONMENT with dev, staging, or prod
ENVIRONMENT=dev
PROJECT=my-invoicemanager-dev

# PostgreSQL user
echo -n "postgres" | \
  gcloud secrets versions add "invoicemanager-${ENVIRONMENT}-postgres-user" \
    --project="${PROJECT}" --data-file=-

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

## Step 5: Install External Secrets Operator in GKE

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

## Step 6: First Deployment

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
