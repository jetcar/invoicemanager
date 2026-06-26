# InvoiceManager — Infrastructure Architecture

> Auto-generated on **2026-06-26 03:06 UTC** by [`scripts/generate_architecture_diagram.py`](../scripts/generate_architecture_diagram.py).
> Re-runs daily via GitHub Actions ([`.github/workflows/architecture-diagram.yml`](../.github/workflows/architecture-diagram.yml))
> and on every push that touches infrastructure files.

---

## Local Development Environment

Runs entirely via `docker-compose up`.
HAProxy listens on `:80`/`:443` and routes by URL path prefix to the relevant FastAPI microservice.

```mermaid
graph TB
  Client(["🌐 Client / Browser"])

  subgraph Gateway["API Gateway"]
    HAProxy["HAProxy\n:80 HTTP  :443 HTTPS  :8404 Stats"]
  end

  subgraph Services["Microservices (FastAPI :8000)"]
    auth_service["auth-service\n/api/v1/auth"]
    company_service["company-service\n/api/v1/companies  /api/v1/organizations"]
    invoice_service["invoice-service\n/api/v1/invoices"]
    supplier_service["supplier-service\n/api/v1/suppliers"]
    notification_service["notification-service\n/api/v1/notifications"]
    audit_service["audit-service\n/api/v1/audit"]
    archive_service["archive-service\n/api/v1/archive"]
  end

  subgraph Databases["PostgreSQL 16 Databases"]
    postgres_auth[("postgres-auth")]
    postgres_company[("postgres-company")]
    postgres_invoice[("postgres-invoice")]
    postgres_supplier[("postgres-supplier")]
    postgres_notification[("postgres-notification")]
    postgres_audit[("postgres-audit")]
    postgres_archive[("postgres-archive")]
  end

  subgraph Messaging["Messaging & Cache"]
    kafka["Kafka :9092\nZookeeper :2181"]
    kafka_ui["Kafka UI :8090"]
    redis["Redis 7.2 :6379"]
  end

  subgraph DevTools["Dev Tools"]
    mailhog["MailHog\n:8025 UI  :1025 SMTP"]
  end

  Client --> HAProxy
  HAProxy --> auth_service & company_service & invoice_service & supplier_service & notification_service & audit_service & archive_service

  auth_service --> postgres_auth & redis & kafka
  company_service --> postgres_company & redis & kafka
  invoice_service --> postgres_invoice & redis & kafka
  supplier_service --> postgres_supplier & redis & kafka
  notification_service --> postgres_notification & redis & kafka
  audit_service --> postgres_audit & kafka
  archive_service --> postgres_archive & postgres_invoice & kafka
  kafka_ui --> kafka
  auth_service -.->|"SMTP"| mailhog
  notification_service -.->|"SMTP"| mailhog
```

---

## GCP Cloud Architecture (dev / staging / production)

Three identical GKE Autopilot clusters — one per environment.
Images are built once and promoted through dev → staging → production.

```mermaid
graph TB
  subgraph GitHub["☁️ GitHub Actions CI/CD"]
    direction TB
    Build["🔨 Build &amp; Push\n(on push to main / workflow_dispatch)"]
    DeployDev["🚀 Deploy → dev\n(automatic)"]
    DeployStaging["🚀 Deploy → staging\n(requires approval)"]
    DeployProd["🚀 Deploy → production\n(requires reviewers)"]
    Build --> DeployDev --> DeployStaging --> DeployProd
  end

  subgraph GCP["☁️ GCP (europe-west1)"]
    AR[["Artifact Registry\n(Docker images)"]]
    SM[["Secret Manager"]]
    WIF[["Workload Identity Federation\n(keyless auth)"]]

    subgraph GKE_dev["GKE Autopilot — DEV"]
      direction TB
      subgraph NS_dev["Namespace: invoicemanager"]
        ESO_dev["External Secrets Operator\n(syncs from Secret Manager)"]
        Ingress_dev["GCE L7 Ingress / Load Balancer"]
        HAP_dev["HAProxy\n(2 replicas)"]
        subgraph SVC_dev["Microservices"]
          auth_dev["auth-service\n2–6 pods (HPA)"]
          company_dev["company-service\n2–6 pods (HPA)"]
          invoice_dev["invoice-service\n2–8 pods (HPA)"]
          supplier_dev["supplier-service\n2–4 pods (HPA)"]
          notification_dev["notification-service\n2–4 pods (HPA)"]
          audit_dev["audit-service\n1 pod"]
          archive_dev["archive-service\n1 pod"]
        end
        subgraph INFRA_dev["In-cluster Infrastructure"]
          kafka_dev["Kafka + Zookeeper"]
          redis_dev["Redis"]
          pg_auth_dev[("auth_db")]
          pg_company_dev[("company_db")]
          pg_invoice_dev[("invoice_db")]
          pg_supplier_dev[("supplier_db")]
          pg_notification_dev[("notification_db")]
          pg_audit_dev[("audit_db")]
          pg_archive_dev[("archive_db")]
        end
        ESO_dev <-->|"sync secrets"| SM
        Ingress_dev --> HAP_dev
        HAP_dev --> SVC_dev
        SVC_dev --> INFRA_dev
      end
    end

    subgraph GKE_staging["GKE Autopilot — STAGING"]
      direction TB
      subgraph NS_staging["Namespace: invoicemanager"]
        ESO_staging["External Secrets Operator\n(syncs from Secret Manager)"]
        Ingress_staging["GCE L7 Ingress / Load Balancer"]
        HAP_staging["HAProxy\n(2 replicas)"]
        subgraph SVC_staging["Microservices"]
          auth_staging["auth-service\n2–6 pods (HPA)"]
          company_staging["company-service\n2–6 pods (HPA)"]
          invoice_staging["invoice-service\n2–8 pods (HPA)"]
          supplier_staging["supplier-service\n2–4 pods (HPA)"]
          notification_staging["notification-service\n2–4 pods (HPA)"]
          audit_staging["audit-service\n1 pod"]
          archive_staging["archive-service\n1 pod"]
        end
        subgraph INFRA_staging["In-cluster Infrastructure"]
          kafka_staging["Kafka + Zookeeper"]
          redis_staging["Redis"]
          pg_auth_staging[("auth_db")]
          pg_company_staging[("company_db")]
          pg_invoice_staging[("invoice_db")]
          pg_supplier_staging[("supplier_db")]
          pg_notification_staging[("notification_db")]
          pg_audit_staging[("audit_db")]
          pg_archive_staging[("archive_db")]
        end
        ESO_staging <-->|"sync secrets"| SM
        Ingress_staging --> HAP_staging
        HAP_staging --> SVC_staging
        SVC_staging --> INFRA_staging
      end
    end

    subgraph GKE_prod["GKE Autopilot — PROD"]
      direction TB
      subgraph NS_prod["Namespace: invoicemanager"]
        ESO_prod["External Secrets Operator\n(syncs from Secret Manager)"]
        Ingress_prod["GCE L7 Ingress / Load Balancer"]
        HAP_prod["HAProxy\n(2 replicas)"]
        subgraph SVC_prod["Microservices"]
          auth_prod["auth-service\n2–6 pods (HPA)"]
          company_prod["company-service\n2–6 pods (HPA)"]
          invoice_prod["invoice-service\n2–8 pods (HPA)"]
          supplier_prod["supplier-service\n2–4 pods (HPA)"]
          notification_prod["notification-service\n2–4 pods (HPA)"]
          audit_prod["audit-service\n1 pod"]
          archive_prod["archive-service\n1 pod"]
        end
        subgraph INFRA_prod["In-cluster Infrastructure"]
          kafka_prod["Kafka + Zookeeper"]
          redis_prod["Redis"]
          pg_auth_prod[("auth_db")]
          pg_company_prod[("company_db")]
          pg_invoice_prod[("invoice_db")]
          pg_supplier_prod[("supplier_db")]
          pg_notification_prod[("notification_db")]
          pg_audit_prod[("audit_db")]
          pg_archive_prod[("archive_db")]
        end
        ESO_prod <-->|"sync secrets"| SM
        Ingress_prod --> HAP_prod
        HAP_prod --> SVC_prod
        SVC_prod --> INFRA_prod
      end
    end

    Build -->|"docker push"| AR
    Build & DeployDev & DeployStaging & DeployProd <-->|"auth"| WIF
    DeployDev -->|"helm upgrade"| GKE_dev
    DeployStaging -->|"helm upgrade"| GKE_staging
    DeployProd -->|"helm upgrade"| GKE_prod
    GKE_dev & GKE_staging & GKE_prod -->|"pull images"| AR
  end
```

---

## Key Components

| Component | Technology | Notes |
|-----------|-----------|-------|
| API Gateway | HAProxy 2.9 | Path-based routing, health checks, stats UI |
| Microservices | FastAPI (Python) | 7 services, each with its own PostgreSQL DB |
| Message bus | Apache Kafka 7.6 + Zookeeper | Event-driven communication between services |
| Cache / sessions | Redis 7.2 | Per-service DB index (0–4) |
| Container runtime | Docker / GKE Autopilot | Local: Docker Compose; Cloud: GKE Autopilot |
| Image registry | GCP Artifact Registry | `europe-west1` region |
| Secret management | GCP Secret Manager + External Secrets Operator | No secrets in code or CI env vars |
| Auth | Workload Identity Federation | Keyless GCP auth from GitHub Actions |
| IaC | Terraform 1.9+ (GCS remote state) | Modules: network, GKE, IAM, AR, Secret Manager, WIF |
| Helm chart | `k8s/helm/invoicemanager` | Single chart, per-env values files |
| CI/CD | GitHub Actions | build → dev → staging → prod (with approvals) |
| Autoscaling | HPA | Most services: 2–8 pods; audit/archive: 1–2 pods |

---

## Service → Route Mapping (HAProxy)

| Route prefix | Service |
|-------------|---------|
| `/api/v1/auth` | `auth-service` |
| `/api/v1/companies` | `company-service` |
| `/api/v1/organizations` | `company-service` |
| `/api/v1/invoices` | `invoice-service` |
| `/api/v1/suppliers` | `supplier-service` |
| `/api/v1/notifications` | `notification-service` |
| `/api/v1/audit` | `audit-service` |
| `/api/v1/archive` | `archive-service` |

---

## Terraform Modules (dev environment)

- `apis`
- `network`
- `gke`
- `artifact_registry`
- `iam`
- `secrets`
- `workload_identity`
