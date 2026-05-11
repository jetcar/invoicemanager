# InvoiceManager

A comprehensive **multi-tenant invoice management system** built on a microservices architecture.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         HAProxy (port 80/443)                    │
│              Routes /api/v1/* to corresponding services          │
└────────┬──────────┬──────────┬──────────┬──────────┬────────────┘
         │          │          │          │          │
    auth-svc  company-svc  invoice-svc  supplier  notification
         │          │          │          │          │
         └──────────┴────┬─────┴──────────┴──────────┘
                         │
               Kafka event bus  ←→  audit-svc / archive-svc
                         │
               Redis (sessions, cache)
```

## Services

| Service | Responsibility |
|---|---|
| **auth-service** | User registration, login, JWT, 2FA (TOTP), QR/magic-link passwordless login, invitations |
| **company-service** | Companies (self-registration + superadmin verification), organizations, member roles |
| **invoice-service** | Purchase & sales invoices, e-invoice parsing (Estonian 1.2 + UBL 2.1), confirmation flow, transaction rows |
| **supplier-service** | Company-specific and shared supplier lists |
| **notification-service** | Email (SMTP) and push notifications (Firebase FCM) |
| **audit-service** | Immutable audit log of all user actions |
| **archive-service** | Cold storage archiving of old invoices |

## Technology Stack

- **Backend**: Python 3.12, FastAPI, SQLAlchemy async
- **Databases**: PostgreSQL 16 (one per service)
- **Cache / Sessions**: Redis 7
- **Message broker**: Apache Kafka
- **Load balancer**: HAProxy 2.9
- **Containerisation**: Docker Compose
- **Mobile**: Android (Kotlin, WebView + FCM + ZXing QR)

## Getting Started

### Prerequisites

- Docker & Docker Compose
- (Optional) Python 3.12 for local development
- (Optional) Android Studio for mobile

### 1. Configure environment

```bash
cp .env.example .env
# Edit .env and set strong passwords + your SMTP/Firebase credentials
```

### 2. Start all services

```bash
docker compose up -d
```

### 3. Access

| Endpoint | URL |
|---|---|
| API Gateway | http://localhost |
| Kafka UI | http://localhost:8090 |
| MailHog (dev email) | http://localhost:8025 |
| HAProxy stats | http://localhost:8404/stats |

## Key Features

### Authentication & Users
- Full registration form with email verification
- JWT access + refresh tokens with rotation
- TOTP-based 2FA (authenticator app)
- Passwordless login via magic email link
- QR-code login (desktop shows QR, mobile app scans to confirm)
- Invitation flow: invite by email → accept → create or link account

### Companies & Organisations
- Self-registration with superadmin verification
- User roles per company: **admin**, **processor**, **auditor**
- Organisations group multiple companies
- Each company has an API key for external invoice import

### Invoices
#### Purchase Invoices
- Manual creation, e-invoice XML upload (Estonian 1.2 + UBL 2.1 auto-detected)
- Multi-step approval workflow with comments
- Transaction rows: create, edit, split, merge
- Automation rules: pattern-match to auto-generate rows and assign reviewers

#### Sales Invoices
- Manual creation and API import via company API key
- Export to external APIs / ERP

### Supplier Management
- Company-specific private suppliers + shared global list

### Archive & Audit
- Cold storage for old invoices
- Immutable audit log for every user action

### Mobile App (Android)
- WebView wrapping the web UI
- FCM push notifications for workflow assignments
- QR code scanner for passwordless login
- Encrypted token storage (Android Keystore)

## Running Tests

```bash
cd services/invoice-service
pip install lxml pytest
python -m pytest tests/ -v
```

## Spec-First Workflow (Invoice Service)

Invoice service now uses a **spec-first OpenAPI workflow** with a committed, versioned contract:

- Contract source: `/home/runner/work/invoicemanager/invoicemanager/specs/invoice-service/v1/openapi.json`
- Generated client/DTOs: `/home/runner/work/invoicemanager/invoicemanager/services/invoice-service/generated/client/python/`
- Generated contract tests: `/home/runner/work/invoicemanager/invoicemanager/services/invoice-service/tests/generated/`

### Regenerate artifacts after spec changes

```bash
cd /home/runner/work/invoicemanager/invoicemanager
python scripts/spec/generate_invoice_artifacts.py
```

### Run invoice service tests (including generated contract checks)

```bash
cd /home/runner/work/invoicemanager/invoicemanager/services/invoice-service
pip install -r requirements.txt -r tests/requirements-test.txt
PYTHONPATH=. python -m pytest tests/ -v
```

### Breaking-change check

```bash
cd /home/runner/work/invoicemanager/invoicemanager
python scripts/spec/check_openapi_breaking.py \
  --base /path/to/base/openapi.json \
  --head specs/invoice-service/v1/openapi.json
```

### PR automation

GitHub Actions workflow: `/home/runner/work/invoicemanager/invoicemanager/.github/workflows/spec-first-invoice.yml`

For pull requests touching invoice-service/spec tooling, CI will:

1. Regenerate spec-driven artifacts
2. Fail if generated output is not committed
3. Run invoice tests (existing + generated contract tests)
4. Detect breaking OpenAPI changes against base branch

If a breaking change is intentional, add PR label: `allow-breaking-openapi`.

## Project Structure

```
invoicemanager/
├── docker-compose.yml
├── .env.example
├── haproxy/haproxy.cfg
├── services/
│   ├── auth-service/
│   ├── company-service/
│   ├── invoice-service/
│   │   └── tests/          # E-invoice parser unit tests
│   ├── supplier-service/
│   ├── notification-service/
│   ├── audit-service/
│   └── archive-service/
└── mobile/android/         # Android app (Kotlin)
```
