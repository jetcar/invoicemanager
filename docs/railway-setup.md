# Railway Setup Guide

This guide deploys InvoiceManager to Railway from this monorepo.

## 1) Create project and services

1. In Railway, create a new project connected to this repository.
2. Create one service per path:
   - `./haproxy`
   - `./services/auth-service`
   - `./services/company-service`
   - `./services/invoice-service`
   - `./services/supplier-service`
   - `./services/notification-service`
   - `./services/audit-service`
   - `./services/archive-service`

Use Dockerfile deploy mode for each service.

## 2) Add data services first

Create and connect:

- PostgreSQL (one database per microservice: `auth_db`, `company_db`, `invoice_db`, `supplier_db`, `notification_db`, `audit_db`, `archive_db`)
- Redis
- Kafka-compatible broker (managed Kafka or external provider)

## 3) Networking model

- Expose **only** `haproxy` publicly.
- Keep all FastAPI services private/internal.
- Keep data services private/internal.

## 4) Shared required environment variables

Set the same `SECRET_KEY` on **all API services**:

- `auth-service`
- `company-service`
- `invoice-service`
- `supplier-service`
- `notification-service`
- `audit-service`
- `archive-service`

Use a long random production value.

## 5) Service environment variable matrix

Values come from `.env.example` and service configs.

### auth-service

- `DATABASE_URL=postgresql+asyncpg://<user>:<password>@<host>:5432/auth_db`
- `REDIS_URL=redis://:<password>@<redis-host>:6379/0`
- `KAFKA_BOOTSTRAP_SERVERS=<kafka-host>:9092`
- `SECRET_KEY=<same-shared-secret-for-all-services>`
- `ACCESS_TOKEN_EXPIRE_MINUTES=60`
- `REFRESH_TOKEN_EXPIRE_DAYS=30`
- `SMTP_HOST=<smtp-host>`
- `SMTP_PORT=<smtp-port>`
- `SMTP_USER=<smtp-user>`
- `SMTP_PASSWORD=<smtp-password>`
- `SMTP_FROM=<from-email>`
- `APP_BASE_URL=<public-haproxy-url>`

### company-service

- `DATABASE_URL=postgresql+asyncpg://<user>:<password>@<host>:5432/company_db`
- `REDIS_URL=redis://:<password>@<redis-host>:6379/1`
- `KAFKA_BOOTSTRAP_SERVERS=<kafka-host>:9092`
- `SECRET_KEY=<same-shared-secret-for-all-services>`

### invoice-service

- `DATABASE_URL=postgresql+asyncpg://<user>:<password>@<host>:5432/invoice_db`
- `REDIS_URL=redis://:<password>@<redis-host>:6379/2`
- `KAFKA_BOOTSTRAP_SERVERS=<kafka-host>:9092`
- `SECRET_KEY=<same-shared-secret-for-all-services>`

### supplier-service

- `DATABASE_URL=postgresql+asyncpg://<user>:<password>@<host>:5432/supplier_db`
- `REDIS_URL=redis://:<password>@<redis-host>:6379/3`
- `KAFKA_BOOTSTRAP_SERVERS=<kafka-host>:9092`
- `SECRET_KEY=<same-shared-secret-for-all-services>`

### notification-service

- `DATABASE_URL=postgresql+asyncpg://<user>:<password>@<host>:5432/notification_db`
- `REDIS_URL=redis://:<password>@<redis-host>:6379/4`
- `KAFKA_BOOTSTRAP_SERVERS=<kafka-host>:9092`
- `SECRET_KEY=<same-shared-secret-for-all-services>`
- `SMTP_HOST=<smtp-host>`
- `SMTP_PORT=<smtp-port>`
- `SMTP_USER=<smtp-user>`
- `SMTP_PASSWORD=<smtp-password>`
- `SMTP_FROM=<from-email>`
- `FIREBASE_CREDENTIALS_JSON=<firebase-json-string-or-empty>`

### audit-service

- `DATABASE_URL=postgresql+asyncpg://<user>:<password>@<host>:5432/audit_db`
- `KAFKA_BOOTSTRAP_SERVERS=<kafka-host>:9092`
- `SECRET_KEY=<same-shared-secret-for-all-services>`

### archive-service

- `DATABASE_URL=postgresql+asyncpg://<user>:<password>@<host>:5432/archive_db`
- `KAFKA_BOOTSTRAP_SERVERS=<kafka-host>:9092`
- `SECRET_KEY=<same-shared-secret-for-all-services>`
- `ARCHIVE_THRESHOLD_DAYS=365`

## 6) Ports and health checks

- Every FastAPI service listens on port `8000`.
- Health endpoint: `/health`.
- Configure Railway health checks for each app service to `/health`.

## 7) HAProxy backend host mapping for Railway

The HAProxy Docker image now renders backend hostnames from env vars.

Set these variables on the `haproxy` service to your Railway internal service DNS names:

- `AUTH_BACKEND_HOST`
- `COMPANY_BACKEND_HOST`
- `INVOICE_BACKEND_HOST`
- `SUPPLIER_BACKEND_HOST`
- `NOTIFICATION_BACKEND_HOST`
- `AUDIT_BACKEND_HOST`
- `ARCHIVE_BACKEND_HOST`

If your internal names match defaults (`auth-service`, `company-service`, etc.), you can leave them unset.

## 8) Verify deployment

After deploy, test through the public HAProxy URL:

- `GET /health`
- `GET /api/v1/auth/...`
- `GET /api/v1/companies/...`

Then validate end-to-end auth and one invoice flow.

## 9) Hardening after first stable deploy

- Enable autoscaling for HAProxy and high-traffic services.
- Enable Railway alerts and log drains.
- Rotate production secrets regularly.
