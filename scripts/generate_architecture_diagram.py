#!/usr/bin/env python3
"""
Generate docs/architecture.md with up-to-date Mermaid architecture diagrams.

Reads the actual configuration files so the diagram stays in sync with the
codebase:
  - docker-compose.yml            → local-dev diagram
  - haproxy/haproxy.cfg           → routing rules
  - k8s/helm/invoicemanager/values.yaml → k8s service / replica config
  - infra/terraform/environments/dev/main.tf → GCP module list
  - .github/workflows/build-deploy.yml → CI/CD pipeline shape
"""

from __future__ import annotations

import re
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import yaml
except ImportError:
    print("PyYAML not found – installing…", flush=True)
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet", "pyyaml"])
    import yaml

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
DOCKER_COMPOSE = ROOT / "docker-compose.yml"
HAPROXY_CFG = ROOT / "haproxy" / "haproxy.cfg"
HELM_VALUES = ROOT / "k8s" / "helm" / "invoicemanager" / "values.yaml"
TERRAFORM_MAIN = ROOT / "infra" / "terraform" / "environments" / "dev" / "main.tf"
BUILD_DEPLOY = ROOT / ".github" / "workflows" / "build-deploy.yml"
OUTPUT = ROOT / "docs" / "architecture.md"


# ── Helpers ───────────────────────────────────────────────────────────────────

def load_yaml(path: Path) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def parse_haproxy_routes(cfg_text: str) -> list[tuple[str, str]]:
    """Return list of (path_prefix, backend) from haproxy ACL rules."""
    acl_map: dict[str, str] = {}
    routes: list[tuple[str, str]] = []
    for line in cfg_text.splitlines():
        line = line.strip()
        m = re.match(r"acl\s+(\w+)\s+path_beg\s+(.+)", line)
        if m:
            acl_map[m.group(1)] = m.group(2).strip()
        m = re.match(r"use_backend\s+(\w+)\s+if\s+(\w+)", line)
        if m:
            backend, acl = m.group(1), m.group(2)
            prefix = acl_map.get(acl, acl)
            routes.append((prefix, backend))
    return routes


def parse_terraform_modules(tf_text: str) -> list[str]:
    """Return list of module names from a terraform file."""
    return re.findall(r'module\s+"(\w+)"\s*\{', tf_text)


def parse_environments(build_deploy_text: str) -> list[str]:
    """Return deployment environment names from build-deploy workflow."""
    return re.findall(r'environment:\s*(\w+)', build_deploy_text)


# ── Diagram builders ──────────────────────────────────────────────────────────

def build_local_dev_diagram(compose: dict, haproxy_routes: list[tuple[str, str]]) -> str:
    """Build Mermaid graph for the local Docker-Compose environment."""
    services = compose.get("services", {})

    # Categorise services
    microservices: list[str] = []
    databases: list[tuple[str, str]] = []   # (service_key, db_name)
    infra: list[str] = []
    dev_tools: list[str] = []
    gateway: list[str] = []

    db_pattern = re.compile(r"POSTGRES_DB:\s*(\S+)")

    for svc, cfg in services.items():
        image = cfg.get("image", "")
        build = cfg.get("build")
        env = cfg.get("environment", {})

        if svc == "haproxy":
            gateway.append(svc)
        elif build:
            microservices.append(svc)
        elif "postgres" in svc:
            # Extract db name from environment
            env_str = str(env)
            m = db_pattern.search(env_str)
            db_name = m.group(1) if m else svc
            databases.append((svc, db_name))
        elif svc in ("kafka", "redis", "kafka-ui"):
            infra.append(svc)
        elif svc == "zookeeper":
            pass  # shown as part of the Kafka node label
        else:
            dev_tools.append(svc)

    # Build routing label map: backend_name → path prefixes
    route_map: dict[str, list[str]] = {}
    for prefix, backend in haproxy_routes:
        route_map.setdefault(backend, []).append(prefix)

    # Map microservice → backend name (haproxy config uses <svc>_backend)
    svc_to_backend = {s: f"{s.replace('-service', '')}_backend" for s in microservices}

    lines: list[str] = ["graph TB"]
    lines.append('  Client(["🌐 Client / Browser"])')
    lines.append("")

    # Gateway
    lines.append('  subgraph Gateway["API Gateway"]')
    lines.append('    HAProxy["HAProxy\\n:80 HTTP  :443 HTTPS  :8404 Stats"]')
    lines.append("  end")
    lines.append("")

    # Microservices
    lines.append('  subgraph Services["Microservices (FastAPI :8000)"]')
    for svc in microservices:
        backend = svc_to_backend.get(svc, "")
        paths = route_map.get(backend, [])
        label = svc
        if paths:
            label += "\\n" + "  ".join(paths)
        safe_id = svc.replace("-", "_")
        lines.append(f'    {safe_id}["{label}"]')
    lines.append("  end")
    lines.append("")

    # Databases
    lines.append('  subgraph Databases["PostgreSQL 16 Databases"]')
    for db_svc, db_name in databases:
        safe_id = db_svc.replace("-", "_")
        lines.append(f'    {safe_id}[("{db_name}")]')
    lines.append("  end")
    lines.append("")

    # Infrastructure
    lines.append('  subgraph Messaging["Messaging & Cache"]')
    for svc in infra:
        safe_id = svc.replace("-", "_")
        if svc == "kafka":
            lines.append(f'    {safe_id}["Kafka :9092\\nZookeeper :2181"]')
        elif svc == "kafka-ui":
            lines.append(f'    {safe_id}["Kafka UI :8090"]')
        elif svc == "redis":
            lines.append(f'    {safe_id}["Redis 7.2 :6379"]')
        else:
            lines.append(f'    {safe_id}["{svc}"]')
    lines.append("  end")
    lines.append("")

    # Dev tools
    if dev_tools:
        lines.append('  subgraph DevTools["Dev Tools"]')
        for svc in dev_tools:
            safe_id = svc.replace("-", "_")
            if svc == "mailhog":
                lines.append(f'    {safe_id}["MailHog\\n:8025 UI  :1025 SMTP"]')
            else:
                lines.append(f'    {safe_id}["{svc}"]')
        lines.append("  end")
        lines.append("")

    # Edges: client → gateway → services
    lines.append("  Client --> HAProxy")
    svc_ids = " & ".join(s.replace("-", "_") for s in microservices)
    lines.append(f"  HAProxy --> {svc_ids}")
    lines.append("")

    # Edges: services → databases + infra
    # Build depends_on map from compose
    # Track which postgres-invoice edge already exists so archive dotted edge
    # doesn't create a confusing duplicate.
    archive_already_has_invoice_edge = False
    for svc in microservices:
        safe_svc = svc.replace("-", "_")
        cfg = services[svc]
        deps = cfg.get("depends_on", [])
        if isinstance(deps, dict):
            deps = list(deps.keys())

        db_deps = [d.replace("-", "_") for d in deps if "postgres" in d]
        infra_deps = [d.replace("-", "_") for d in deps if d in ("redis", "kafka")]

        all_deps = db_deps + infra_deps
        if all_deps:
            lines.append(f"  {safe_svc} --> {' & '.join(all_deps)}")
        if svc == "archive-service" and "postgres_invoice" in db_deps:
            archive_already_has_invoice_edge = True

    # archive-service reads from postgres-invoice (annotated edge)
    if "archive-service" in microservices and not archive_already_has_invoice_edge:
        lines.append('  archive_service -.->|"reads invoice DB"| postgres_invoice')

    # kafka-ui → kafka
    if "kafka-ui" in infra and "kafka" in infra:
        lines.append("  kafka_ui --> kafka")

    # SMTP: services that use mailhog
    for svc in microservices:
        env = services[svc].get("environment", {})
        if "SMTP_HOST" in str(env) and dev_tools:
            safe_svc = svc.replace("-", "_")
            lines.append(f'  {safe_svc} -.->|"SMTP"| mailhog')

    return "\n".join(lines)


def build_gcp_cloud_diagram(
    helm: dict,
    tf_modules: list[str],
    environments: list[str],
) -> str:
    """Build Mermaid graph for the GCP cloud architecture."""
    services_cfg = helm.get("services", {})
    infra_cfg = helm.get("infrastructure", {})
    global_cfg = helm.get("global", {})

    region = global_cfg.get("imageRegistry", "europe-west1-docker.pkg.dev").split("-docker.pkg.dev")[0]
    if "/" in region:
        region = "europe-west1"

    lines: list[str] = ["graph TB"]

    # GitHub CI/CD
    lines.append('  subgraph GitHub["☁️ GitHub Actions CI/CD"]')
    lines.append('    direction TB')
    lines.append('    Build["🔨 Build &amp; Push\\n(on push to main / workflow_dispatch)"]')
    lines.append('    DeployDev["🚀 Deploy → dev\\n(automatic)"]')
    lines.append('    DeployStaging["🚀 Deploy → staging\\n(requires approval)"]')
    lines.append('    DeployProd["🚀 Deploy → production\\n(requires reviewers)"]')
    lines.append('    Build --> DeployDev --> DeployStaging --> DeployProd')
    lines.append("  end")
    lines.append("")

    # GCP shared services
    lines.append(f'  subgraph GCP["☁️ GCP ({region})"]')
    lines.append('    AR[["Artifact Registry\\n(Docker images)"]]')
    lines.append('    SM[["Secret Manager"]]')
    lines.append('    WIF[["Workload Identity Federation\\n(keyless auth)"]]')
    lines.append("")

    # Three GKE environments
    for env in ["dev", "staging", "prod"]:
        env_label = env.upper()
        lines.append(f'    subgraph GKE_{env}["GKE Autopilot — {env_label}"]')
        lines.append(f'      direction TB')
        lines.append(f'      subgraph NS_{env}["Namespace: invoicemanager"]')
        lines.append(f'        ESO_{env}["External Secrets Operator\\n(syncs from Secret Manager)"]')
        lines.append(f'        Ingress_{env}["GCE L7 Ingress / Load Balancer"]')
        lines.append(f'        HAP_{env}["HAProxy\\n(2 replicas)"]')
        lines.append(f'        subgraph SVC_{env}["Microservices"]')

        for svc_key, svc_cfg in services_cfg.items():
            svc_name = svc_cfg.get("name", svc_key)
            hpa = svc_cfg.get("hpa", {})
            if hpa.get("enabled"):
                replicas = f'{hpa["minReplicas"]}–{hpa["maxReplicas"]} pods (HPA)'
            else:
                replicas = f'{svc_cfg.get("replicas", 1)} pod'
            safe_id = f"{svc_key}_{env}"
            lines.append(f'          {safe_id}["{svc_name}\\n{replicas}"]')

        lines.append(f'        end')  # SVC

        # In-cluster infra
        lines.append(f'        subgraph INFRA_{env}["In-cluster Infrastructure"]')
        if infra_cfg.get("kafka", {}).get("enabled"):
            lines.append(f'          kafka_{env}["Kafka + Zookeeper"]')
        if infra_cfg.get("redis", {}).get("enabled"):
            lines.append(f'          redis_{env}["Redis"]')
        dbs = infra_cfg.get("postgres", {}).get("databases", [])
        for db in dbs:
            db_id = f'pg_{db["name"]}_{env}'
            lines.append(f'          {db_id}[("{db["db"]}")]')
        lines.append(f'        end')  # INFRA

        # Edges inside namespace
        lines.append(f'        ESO_{env} <-->|"sync secrets"| SM')
        lines.append(f'        Ingress_{env} --> HAP_{env}')
        lines.append(f'        HAP_{env} --> SVC_{env}')
        svc_block = f'SVC_{env}'
        infra_block = f'INFRA_{env}'
        lines.append(f'        {svc_block} --> {infra_block}')

        lines.append(f'      end')  # NS
        lines.append(f'    end')  # GKE
        lines.append("")

    # CI/CD → GCP edges
    lines.append('    Build -->|"docker push"| AR')
    lines.append('    Build & DeployDev & DeployStaging & DeployProd <-->|"auth"| WIF')
    lines.append('    DeployDev -->|"helm upgrade"| GKE_dev')
    lines.append('    DeployStaging -->|"helm upgrade"| GKE_staging')
    lines.append('    DeployProd -->|"helm upgrade"| GKE_prod')
    lines.append('    GKE_dev & GKE_staging & GKE_prod -->|"pull images"| AR')

    lines.append("  end")  # GCP

    return "\n".join(lines)


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    print("Reading configuration files…")
    compose = load_yaml(DOCKER_COMPOSE)
    haproxy_text = HAPROXY_CFG.read_text()
    helm = load_yaml(HELM_VALUES)
    tf_text = TERRAFORM_MAIN.read_text()
    build_deploy_text = BUILD_DEPLOY.read_text()

    haproxy_routes = parse_haproxy_routes(haproxy_text)
    tf_modules = parse_terraform_modules(tf_text)
    environments = list(dict.fromkeys(parse_environments(build_deploy_text)))

    print("Generating diagrams…")
    local_diagram = build_local_dev_diagram(compose, haproxy_routes)
    cloud_diagram = build_gcp_cloud_diagram(helm, tf_modules, environments)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    content = f"""\
# InvoiceManager — Infrastructure Architecture

> Auto-generated on **{now}** by [`scripts/generate_architecture_diagram.py`](../scripts/generate_architecture_diagram.py).
> Re-runs daily via GitHub Actions ([`.github/workflows/architecture-diagram.yml`](../.github/workflows/architecture-diagram.yml))
> and on every push that touches infrastructure files.

---

## Local Development Environment

Runs entirely via `docker-compose up`.
HAProxy listens on `:80`/`:443` and routes by URL path prefix to the relevant FastAPI microservice.

```mermaid
{local_diagram}
```

---

## GCP Cloud Architecture (dev / staging / production)

Three identical GKE Autopilot clusters — one per environment.
Images are built once and promoted through dev → staging → production.

```mermaid
{cloud_diagram}
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
{chr(10).join(f"| `{prefix}` | `{backend.replace('_backend', '-service')}` |" for prefix, backend in haproxy_routes if "health" not in backend)}

---

## Terraform Modules (dev environment)

{chr(10).join(f"- `{m}`" for m in tf_modules)}
"""

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(content)
    print(f"✅  Written to {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
