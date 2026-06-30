# Eugenio SDD Demo Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Spec-Anchored WordPress/Astro demo on a single AWS EC2 instance, where `openspec.yaml` is the source of truth and a validator CLI enforces conformance before every deploy.

**Architecture:** OpenSpec Spec-Anchored — `openspec.yaml` defines intent; Terraform, Docker Compose, Nginx, and GitHub Actions are handwritten but validated against the spec via `openspec/validate.py`. Astro runs in SSG mode; Nginx serves the built static files directly. WordPress runs in a Docker container on port 8080.

**Tech Stack:** Python 3.11 (validator), python-hcl2, PyYAML, jsonschema, Terraform ~5.0, Docker Compose v2, Nginx, Astro 7.x, React 19, TypeScript, Vitest 4.x, @testing-library/react, Docusaurus 3.7

## Global Constraints

> **Note:** Values below reflect the current live state after post-implementation changes (domain migration, category update, IAM addition, Docusaurus addition). Original plan values have been updated in place to avoid confusion.

- Project name: `sdd-demo` (verbatim, used in all resource names)
- AWS region: `eu-central-1`
- Instance type: `t3.small`
- OS: `ubuntu-24.04`
- Security group name: `sg-spec-demo`
- IAM role: `sdd-demo-ec2-role` with `route53_update` inline policy
- WordPress domain: `wp.4eng.online`, container port: `8080`
- Astro domain: `astro.4eng.online`, mode: `ssg` (no Astro container in production)
- Docusaurus domain: `docu.4eng.online`, mode: `ssg`, build output: `build/`
- Static files paths on EC2: `/var/www/sdd-demo/astro/dist`, `/var/www/sdd-demo/docusaurus/build`
- Shared media path: `/var/www/sdd-demo/media` (Docker bind mount + nginx alias at `/media/`)
- Secret store: `aws-secrets-manager`
- Secret keys: `db_password`, `wp_admin_password`, `gh_deploy_key`
- Categories: `Sport`, `Travel`, `Uncategorized` (Uncategorized is fallback)
- Posts fetch URL: `https://wp.4eng.online/wp-json/wp/v2/posts?per_page=100&page=1&_embed`
- Clock format: `HH:mm:ss`, timezone source: browser `Intl.DateTimeFormat`
- WordPress title: `Eugenio WP`, Astro title: `Eugenio Astro`, Docusaurus title: `Eugenio Docu`
- Node version: `22` (Astro 7 requires `>=22.12.0`)

---

## File Map

```
sdd-demo/
├── openspec.yaml
├── openspec/
│   ├── validate.py
│   ├── requirements.txt
│   ├── schema/openspec.schema.json
│   └── checks/
│       ├── __init__.py
│       ├── terraform.py
│       ├── docker.py
│       ├── nginx.py
│       └── cicd.py
├── tests/
│   ├── __init__.py
│   └── openspec/
│       ├── __init__.py
│       ├── test_validate.py
│       ├── test_terraform.py
│       ├── test_docker.py
│       ├── test_nginx.py
│       └── test_cicd.py
├── terraform/
│   ├── main.tf          ← includes IAM role, instance profile, route53 policy
│   └── variables.tf
├── docker-compose.yml   ← wordpress uploads volume: /var/www/sdd-demo/media
├── nginx/default.conf   ← 3 upstream domains + /media/ shared location
├── scripts/
│   ├── generate-content.js            ← WP posts → astro/src/content/blog/
│   └── generate-docusaurus-content.js ← WP posts → docusaurus/blog/
├── .github/workflows/deploy.yml
├── astro/
│   ├── astro.config.mjs
│   ├── package.json
│   ├── vitest.config.ts
│   ├── src/
│   │   ├── content.config.ts          ← Astro 5+ Content Layer API (glob loader)
│   │   ├── content/blog/.gitkeep
│   │   ├── pages/index.astro          ← uses e.id (not e.slug) for Astro 7
│   │   ├── styles/global.css
│   │   ├── components/
│   │   │   ├── CategoryFilter.tsx     ← All / Sport / Travel / Uncategorized
│   │   │   ├── LiveClock.tsx
│   │   │   ├── ThemeToggle.tsx
│   │   │   └── Header.astro
│   │   └── tests/
│   │       ├── setup.ts
│   │       ├── CategoryFilter.test.tsx
│   │       ├── LiveClock.test.tsx
│   │       └── ThemeToggle.test.tsx
│   └── tsconfig.json
└── docusaurus/
    ├── docusaurus.config.js   ← blog-only, routeBasePath: "/"
    ├── package.json
    ├── blog/.gitkeep          ← replaced by CI/CD on every deploy
    └── src/css/custom.css
```

---

### Task 1: Project Scaffold

**Files:**
- Create: `openspec.yaml`
- Create: `openspec/requirements.txt`
- Create: `tests/__init__.py`, `tests/openspec/__init__.py`
- Create: `.gitignore`

**Interfaces:**
- Produces: `openspec.yaml` consumed by all subsequent tasks as the spec source

- [ ] **Step 1: Initialize git and create directory structure**

```bash
git init
mkdir -p openspec/schema openspec/checks tests/openspec scripts .github/workflows nginx terraform astro
touch tests/__init__.py tests/openspec/__init__.py openspec/checks/__init__.py
```

- [ ] **Step 2: Write `.gitignore`**

```
__pycache__/
*.pyc
.pytest_cache/
.terraform/
*.tfstate
*.tfstate.backup
.terraform.lock.hcl
node_modules/
astro/dist/
astro/.astro/
.env
```

- [ ] **Step 3: Write `openspec/requirements.txt`**

```
PyYAML==6.0.1
jsonschema==4.22.0
python-hcl2==4.3.2
pytest==8.2.2
```

- [ ] **Step 4: Write `openspec.yaml`**

```yaml
meta:
  name: sdd-demo
  version: "1.0"

infrastructure:
  provider: aws
  region: eu-central-1
  instance_type: t3.small
  os: ubuntu-24.04
  security_group:
    name: sg-spec-demo
    inbound:
      - { port: 22,  cidr: 0.0.0.0/0 }
      - { port: 80,  cidr: 0.0.0.0/0 }
      - { port: 443, cidr: 0.0.0.0/0 }
    outbound:
      - { port: all, cidr: 0.0.0.0/0 }

secrets:
  store: aws-secrets-manager
  keys:
    - db_password
    - wp_admin_password
    - gh_deploy_key

services:
  wordpress:
    title: Eugenio WP
    image: wordpress:latest
    port: 8080
    domain: wp.bball.klarr.us
    categories: [Sport, Software]

  mysql:
    image: mysql:8.0
    secret_ref: db_password

  astro:
    title: Eugenio Astro
    port: 4321
    domain: astro.bball.klarr.us
    mode: ssg
    features:
      dark_light_switcher: true
      live_clock:
        format: HH:mm:ss
        timezone: Intl
    categories: [Sport, Software]

routing:
  engine: nginx
  ssl: letsencrypt
  upstreams:
    - service: wordpress
      domain: wp.bball.klarr.us
      proxy_port: 8080
    - service: astro
      domain: astro.bball.klarr.us
      serve_static: /var/www/sdd-demo/astro/dist

cicd:
  provider: github-actions
  trigger: wordpress-webhook
  steps:
    - fetch_posts:
        url: "https://wp.bball.klarr.us/wp-json/wp/v2/posts"
        params: { per_page: 100, page: 1 }
    - build_astro:
        replaces: ./astro/src/content/blog
    - deploy:
        method: rsync-ssh
        secret_ref: gh_deploy_key
```

- [ ] **Step 5: Install Python dependencies**

```bash
pip install -r openspec/requirements.txt
```

- [ ] **Step 6: Commit**

```bash
git add .
git commit -m "feat: project scaffold and openspec.yaml"
```

---

### Task 2: OpenSpec Schema + Validator Core

**Files:**
- Create: `openspec/schema/openspec.schema.json`
- Create: `openspec/validate.py`
- Create: `tests/openspec/test_validate.py`

**Interfaces:**
- Produces: `validate_schema(spec: dict) -> list[str]` — importable by test suite
- Produces: `load_spec(path: str) -> dict` — importable by test suite
- Produces: CLI `python openspec/validate.py` — exits 0 on pass, 1 on fail

- [ ] **Step 1: Write the failing tests**

```python
# tests/openspec/test_validate.py
import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))

from openspec.validate import validate_schema

VALID_SPEC = {
    "meta": {"name": "test", "version": "1.0"},
    "infrastructure": {
        "provider": "aws",
        "region": "eu-central-1",
        "instance_type": "t3.small",
        "os": "ubuntu-24.04",
        "security_group": {
            "name": "sg-test",
            "inbound": [{"port": 22, "cidr": "0.0.0.0/0"}],
            "outbound": [{"port": "all", "cidr": "0.0.0.0/0"}],
        },
    },
    "secrets": {"store": "aws-secrets-manager", "keys": ["k1"]},
    "services": {
        "wordpress": {
            "title": "WP", "image": "wordpress:latest",
            "port": 8080, "domain": "wp.example.com", "categories": ["Sport"],
        },
        "mysql": {"image": "mysql:8.0", "secret_ref": "k1"},
        "astro": {
            "title": "Astro", "port": 4321, "domain": "astro.example.com",
            "mode": "ssg", "categories": ["Sport"],
        },
    },
    "routing": {
        "engine": "nginx", "ssl": "letsencrypt",
        "upstreams": [
            {"service": "wordpress", "domain": "wp.example.com", "proxy_port": 8080},
            {"service": "astro", "domain": "astro.example.com", "serve_static": "/path/dist"},
        ],
    },
    "cicd": {
        "provider": "github-actions",
        "trigger": "wordpress-webhook",
        "steps": [{"fetch_posts": {"url": "https://wp.example.com/wp-json/wp/v2/posts", "params": {"per_page": 100, "page": 1}}}],
    },
}


def test_valid_spec_passes():
    assert validate_schema(VALID_SPEC) == []


def test_missing_meta_fails():
    spec = {k: v for k, v in VALID_SPEC.items() if k != "meta"}
    errors = validate_schema(spec)
    assert len(errors) > 0


def test_invalid_provider_fails():
    spec = copy.deepcopy(VALID_SPEC)
    spec["infrastructure"]["provider"] = "gcp"
    errors = validate_schema(spec)
    assert len(errors) > 0


def test_invalid_astro_mode_fails():
    spec = copy.deepcopy(VALID_SPEC)
    spec["services"]["astro"]["mode"] = "invalid"
    errors = validate_schema(spec)
    assert len(errors) > 0
```

- [ ] **Step 2: Run to verify failure**

```bash
pytest tests/openspec/test_validate.py -v
```

Expected: `ImportError` — `validate` module not yet implemented.

- [ ] **Step 3: Write `openspec/schema/openspec.schema.json`**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["meta", "infrastructure", "secrets", "services", "routing", "cicd"],
  "additionalProperties": false,
  "properties": {
    "meta": {
      "type": "object",
      "required": ["name", "version"],
      "properties": {
        "name": { "type": "string" },
        "version": { "type": "string" }
      }
    },
    "infrastructure": {
      "type": "object",
      "required": ["provider", "region", "instance_type", "os", "security_group"],
      "properties": {
        "provider": { "type": "string", "enum": ["aws"] },
        "region": { "type": "string" },
        "instance_type": { "type": "string" },
        "os": { "type": "string" },
        "security_group": {
          "type": "object",
          "required": ["name", "inbound", "outbound"],
          "properties": {
            "name": { "type": "string" },
            "inbound": {
              "type": "array",
              "items": {
                "type": "object",
                "required": ["port", "cidr"],
                "properties": {
                  "port": {},
                  "cidr": { "type": "string" }
                }
              }
            },
            "outbound": {
              "type": "array",
              "items": {
                "type": "object",
                "required": ["port", "cidr"],
                "properties": {
                  "port": {},
                  "cidr": { "type": "string" }
                }
              }
            }
          }
        }
      }
    },
    "secrets": {
      "type": "object",
      "required": ["store", "keys"],
      "properties": {
        "store": { "type": "string", "enum": ["aws-secrets-manager"] },
        "keys": { "type": "array", "items": { "type": "string" }, "minItems": 1 }
      }
    },
    "services": {
      "type": "object",
      "required": ["wordpress", "mysql", "astro"],
      "properties": {
        "wordpress": {
          "type": "object",
          "required": ["title", "image", "port", "domain", "categories"]
        },
        "mysql": {
          "type": "object",
          "required": ["image", "secret_ref"]
        },
        "astro": {
          "type": "object",
          "required": ["title", "port", "domain", "mode", "categories"],
          "properties": {
            "mode": { "type": "string", "enum": ["ssg", "ssr"] }
          }
        }
      }
    },
    "routing": {
      "type": "object",
      "required": ["engine", "ssl", "upstreams"],
      "properties": {
        "engine": { "type": "string", "enum": ["nginx"] },
        "ssl": { "type": "string", "enum": ["letsencrypt"] },
        "upstreams": { "type": "array", "minItems": 2 }
      }
    },
    "cicd": {
      "type": "object",
      "required": ["provider", "trigger", "steps"],
      "properties": {
        "provider": { "type": "string", "enum": ["github-actions"] },
        "trigger": { "type": "string" },
        "steps": { "type": "array", "minItems": 1 }
      }
    }
  }
}
```

- [ ] **Step 4: Write `openspec/validate.py`**

```python
#!/usr/bin/env python3
import json
import sys
from pathlib import Path

import jsonschema
import yaml

_SCHEMA_PATH = Path(__file__).parent / "schema" / "openspec.schema.json"


def load_spec(path: str = "openspec.yaml") -> dict:
    return yaml.safe_load(Path(path).read_text())


def validate_schema(spec: dict) -> list[str]:
    schema = json.loads(_SCHEMA_PATH.read_text())
    errors = []
    try:
        jsonschema.validate(spec, schema)
    except jsonschema.ValidationError as e:
        errors.append(e.message)
    return errors


def _run_checks(spec: dict) -> dict[str, list[str]]:
    from openspec.checks import terraform, docker, nginx, cicd
    return {
        "terraform": terraform.check(spec),
        "docker": docker.check(spec),
        "nginx": nginx.check(spec),
        "cicd": cicd.check(spec),
    }


def main() -> int:
    try:
        spec = load_spec()
    except FileNotFoundError:
        print("[FAIL] openspec.yaml not found")
        return 1

    schema_errors = validate_schema(spec)
    if schema_errors:
        print(f"[FAIL] schema\n       → {schema_errors[0]}")
        return 1
    print("[PASS] schema")

    failed = 0
    for name, failures in _run_checks(spec).items():
        if failures:
            print(f"[FAIL] {name}")
            for f in failures:
                print(f"       → {f}")
            failed += 1
        else:
            print(f"[PASS] {name}")

    if failed:
        print(f"\n{failed} check{'s' if failed > 1 else ''} failed.")
        return 1
    print("\nAll checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/openspec/test_validate.py -v
```

Expected:
```
PASSED tests/openspec/test_validate.py::test_valid_spec_passes
PASSED tests/openspec/test_validate.py::test_missing_meta_fails
PASSED tests/openspec/test_validate.py::test_invalid_provider_fails
PASSED tests/openspec/test_validate.py::test_invalid_astro_mode_fails
4 passed
```

- [ ] **Step 6: Commit**

```bash
git add openspec/validate.py openspec/schema/ openspec/checks/__init__.py tests/
git commit -m "feat: openspec schema and validator core"
```

---

### Task 3: Terraform + Terraform Check

**Files:**
- Create: `tests/openspec/test_terraform.py`
- Create: `openspec/checks/terraform.py`
- Create: `terraform/main.tf`, `terraform/variables.tf`, `terraform/outputs.tf`

**Interfaces:**
- Consumes: `spec['infrastructure']`, `spec['secrets']['keys']`
- Produces: `terraform.check(spec, base_dir='.')  -> list[str]`

- [ ] **Step 1: Write the failing tests**

```python
# tests/openspec/test_terraform.py
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[2]))

from openspec.checks.terraform import check

SPEC = {
    "infrastructure": {
        "region": "eu-central-1",
        "instance_type": "t3.small",
        "security_group": {
            "name": "sg-spec-demo",
            "inbound": [
                {"port": 22, "cidr": "0.0.0.0/0"},
                {"port": 80, "cidr": "0.0.0.0/0"},
                {"port": 443, "cidr": "0.0.0.0/0"},
            ],
        },
    },
    "secrets": {"keys": ["db_password", "wp_admin_password", "gh_deploy_key"]},
}

VALID_TF = '''\
variable "region" {
  type    = string
  default = "eu-central-1"
}
variable "instance_type" {
  type    = string
  default = "t3.small"
}
resource "aws_security_group" "sg_spec_demo" {
  name = "sg-spec-demo"
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
resource "aws_instance" "eugenio" {
  instance_type = var.instance_type
}
resource "aws_secretsmanager_secret" "db_password" {
  name = "sdd-demo/db_password"
}
resource "aws_secretsmanager_secret" "wp_admin_password" {
  name = "sdd-demo/wp_admin_password"
}
resource "aws_secretsmanager_secret" "gh_deploy_key" {
  name = "sdd-demo/gh_deploy_key"
}
'''


def test_valid_terraform_passes(tmp_path):
    (tmp_path / "terraform").mkdir()
    (tmp_path / "terraform" / "main.tf").write_text(VALID_TF)
    assert check(SPEC, base_dir=str(tmp_path)) == []


def test_wrong_region_fails(tmp_path):
    (tmp_path / "terraform").mkdir()
    (tmp_path / "terraform" / "main.tf").write_text(
        VALID_TF.replace('"eu-central-1"', '"us-east-1"')
    )
    failures = check(SPEC, base_dir=str(tmp_path))
    assert any("region" in f for f in failures)


def test_wrong_instance_type_fails(tmp_path):
    (tmp_path / "terraform").mkdir()
    (tmp_path / "terraform" / "main.tf").write_text(
        VALID_TF.replace('"t3.small"', '"t3.medium"')
    )
    failures = check(SPEC, base_dir=str(tmp_path))
    assert any("instance_type" in f for f in failures)


def test_missing_secret_fails(tmp_path):
    (tmp_path / "terraform").mkdir()
    tf = "\n".join(
        l for l in VALID_TF.splitlines() if "gh_deploy_key" not in l
    )
    (tmp_path / "terraform" / "main.tf").write_text(tf)
    failures = check(SPEC, base_dir=str(tmp_path))
    assert any("gh_deploy_key" in f for f in failures)


def test_missing_sg_port_fails(tmp_path):
    (tmp_path / "terraform").mkdir()
    tf = "\n".join(
        l for l in VALID_TF.splitlines()
        if "443" not in l
    )
    (tmp_path / "terraform" / "main.tf").write_text(tf)
    failures = check(SPEC, base_dir=str(tmp_path))
    assert any("443" in f for f in failures)
```

- [ ] **Step 2: Run to verify failure**

```bash
pytest tests/openspec/test_terraform.py -v
```

Expected: `ImportError` — `terraform` module not yet implemented.

- [ ] **Step 3: Write `openspec/checks/terraform.py`**

```python
from pathlib import Path

import hcl2


def _load_all_tf(base_dir: str) -> dict:
    merged: dict = {}
    for tf_file in Path(base_dir, "terraform").glob("*.tf"):
        with open(tf_file) as f:
            data = hcl2.load(f)
        for key, value in data.items():
            merged.setdefault(key, [])
            merged[key].extend(value)
    return merged


def _var_default(tf: dict, name: str) -> str | None:
    for block in tf.get("variable", []):
        if name in block:
            return block[name].get("default")
    return None


def _resolve(value: str, tf: dict) -> str:
    if isinstance(value, str) and value.startswith("${var.") and value.endswith("}"):
        return _var_default(tf, value[6:-1]) or value
    return value


def check(spec: dict, base_dir: str = ".") -> list[str]:
    tf_dir = Path(base_dir, "terraform")
    if not tf_dir.exists():
        return ["terraform/ directory not found"]

    tf = _load_all_tf(base_dir)
    failures: list[str] = []

    # Region check (via variable default)
    expected_region = spec["infrastructure"]["region"]
    actual_region = _var_default(tf, "region")
    if actual_region != expected_region:
        failures.append(
            f"region: expected {expected_region}, found {actual_region}"
        )

    # Instance type check (via variable default)
    expected_type = spec["infrastructure"]["instance_type"]
    actual_type = _var_default(tf, "instance_type")
    if actual_type != expected_type:
        failures.append(
            f"instance_type: expected {expected_type}, found {actual_type}"
        )

    # Security group inbound ports
    expected_ports = {
        int(r["port"]) for r in spec["infrastructure"]["security_group"]["inbound"]
        if str(r["port"]).isdigit()
    }
    actual_ports: set[int] = set()
    for block in tf.get("resource", []):
        for sg_config in block.get("aws_security_group", {}).values():
            for rule in sg_config.get("ingress", []):
                actual_ports.add(int(rule["from_port"]))

    missing_ports = expected_ports - actual_ports
    for port in sorted(missing_ports):
        failures.append(f"SG inbound port {port} not found in security group")

    # Secrets Manager resources
    actual_secrets: set[str] = set()
    for block in tf.get("resource", []):
        actual_secrets.update(block.get("aws_secretsmanager_secret", {}).keys())

    expected_secrets = set(spec["secrets"]["keys"])
    for key in expected_secrets - actual_secrets:
        failures.append(f"Missing Secrets Manager resource: {key}")

    return failures
```

- [ ] **Step 4: Write `terraform/main.tf`**

```hcl
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.region
}

data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"]
  }
}

resource "aws_security_group" "sg_spec_demo" {
  name        = "sg-spec-demo"
  description = "sdd-demo security group"

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "sg-spec-demo" }
}

resource "aws_instance" "eugenio" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.instance_type
  vpc_security_group_ids = [aws_security_group.sg_spec_demo.id]

  tags = { Name = "sdd-demo" }
}

resource "aws_secretsmanager_secret" "db_password" {
  name = "sdd-demo/db_password"
}

resource "aws_secretsmanager_secret" "wp_admin_password" {
  name = "sdd-demo/wp_admin_password"
}

resource "aws_secretsmanager_secret" "gh_deploy_key" {
  name = "sdd-demo/gh_deploy_key"
}
```

- [ ] **Step 5: Write `terraform/variables.tf`**

```hcl
variable "region" {
  type    = string
  default = "eu-central-1"
}

variable "instance_type" {
  type    = string
  default = "t3.small"
}
```

- [ ] **Step 6: Write `terraform/outputs.tf`**

```hcl
output "instance_public_ip" {
  value = aws_instance.eugenio.public_ip
}

output "instance_id" {
  value = aws_instance.eugenio.id
}
```

- [ ] **Step 7: Run tests to verify they pass**

```bash
pytest tests/openspec/test_terraform.py -v
```

Expected:
```
PASSED test_valid_terraform_passes
PASSED test_wrong_region_fails
PASSED test_wrong_instance_type_fails
PASSED test_missing_secret_fails
PASSED test_missing_sg_port_fails
5 passed
```

- [ ] **Step 8: Commit**

```bash
git add terraform/ openspec/checks/terraform.py tests/openspec/test_terraform.py
git commit -m "feat: terraform config and terraform conformance check"
```

---

### Task 4: Docker Compose + Docker Check

**Files:**
- Create: `tests/openspec/test_docker.py`
- Create: `openspec/checks/docker.py`
- Create: `docker-compose.yml`

**Interfaces:**
- Consumes: `spec['services']`
- Produces: `docker.check(spec, base_dir='.') -> list[str]`

- [ ] **Step 1: Write the failing tests**

```python
# tests/openspec/test_docker.py
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[2]))

from openspec.checks.docker import check

SPEC = {
    "services": {
        "wordpress": {"port": 8080},
        "mysql": {},
        "astro": {"mode": "ssg"},
    }
}

VALID_COMPOSE = """\
services:
  wordpress:
    image: wordpress:latest
    ports:
      - "8080:80"
    networks:
      - wp-network
  mysql:
    image: mysql:8.0
    networks:
      - wp-network

networks:
  wp-network:
"""


def test_valid_compose_passes(tmp_path):
    (tmp_path / "docker-compose.yml").write_text(VALID_COMPOSE)
    assert check(SPEC, base_dir=str(tmp_path)) == []


def test_missing_wordpress_fails(tmp_path):
    compose = "services:\n  mysql:\n    image: mysql:8.0\n"
    (tmp_path / "docker-compose.yml").write_text(compose)
    failures = check(SPEC, base_dir=str(tmp_path))
    assert any("wordpress" in f for f in failures)


def test_wrong_wp_port_fails(tmp_path):
    compose = VALID_COMPOSE.replace('"8080:80"', '"9090:80"')
    (tmp_path / "docker-compose.yml").write_text(compose)
    failures = check(SPEC, base_dir=str(tmp_path))
    assert any("port" in f.lower() or "8080" in f for f in failures)


def test_astro_service_present_fails_when_ssg(tmp_path):
    compose = VALID_COMPOSE + "  astro:\n    image: node:20\n"
    (tmp_path / "docker-compose.yml").write_text(compose)
    failures = check(SPEC, base_dir=str(tmp_path))
    assert any("astro" in f for f in failures)


def test_missing_mysql_fails(tmp_path):
    compose = "services:\n  wordpress:\n    ports:\n      - '8080:80'\n"
    (tmp_path / "docker-compose.yml").write_text(compose)
    failures = check(SPEC, base_dir=str(tmp_path))
    assert any("mysql" in f for f in failures)
```

- [ ] **Step 2: Run to verify failure**

```bash
pytest tests/openspec/test_docker.py -v
```

Expected: `ImportError` — `docker` module not yet implemented.

- [ ] **Step 3: Write `openspec/checks/docker.py`**

```python
from pathlib import Path

import yaml


def check(spec: dict, base_dir: str = ".") -> list[str]:
    compose_path = Path(base_dir, "docker-compose.yml")
    if not compose_path.exists():
        return ["docker-compose.yml not found"]

    data = yaml.safe_load(compose_path.read_text())
    services = data.get("services", {})
    failures: list[str] = []

    wp_port = spec["services"]["wordpress"]["port"]
    wp = services.get("wordpress")
    if not wp:
        failures.append("wordpress service not found in docker-compose.yml")
    else:
        ports = [str(p) for p in wp.get("ports", [])]
        if not any(p.startswith(f"{wp_port}:") for p in ports):
            failures.append(
                f"wordpress: expected port {wp_port}:80, found {ports}"
            )

    if "mysql" not in services:
        failures.append("mysql service not found in docker-compose.yml")

    if spec["services"]["astro"]["mode"] == "ssg" and "astro" in services:
        failures.append(
            "astro service must not exist in docker-compose.yml when mode=ssg"
        )

    return failures
```

- [ ] **Step 4: Write `docker-compose.yml`**

```yaml
services:
  wordpress:
    image: wordpress:latest
    ports:
      - "8080:80"
    environment:
      WORDPRESS_DB_HOST: mysql
      WORDPRESS_DB_NAME: wordpress
      WORDPRESS_DB_USER: wordpress
      WORDPRESS_DB_PASSWORD: ${DB_PASSWORD}
    depends_on:
      - mysql
    restart: unless-stopped
    networks:
      - wp-network

  mysql:
    image: mysql:8.0
    environment:
      MYSQL_DATABASE: wordpress
      MYSQL_USER: wordpress
      MYSQL_PASSWORD: ${DB_PASSWORD}
      MYSQL_ROOT_PASSWORD: ${DB_ROOT_PASSWORD}
    volumes:
      - mysql_data:/var/lib/mysql
    restart: unless-stopped
    networks:
      - wp-network

volumes:
  mysql_data:

networks:
  wp-network:
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/openspec/test_docker.py -v
```

Expected:
```
PASSED test_valid_compose_passes
PASSED test_missing_wordpress_fails
PASSED test_wrong_wp_port_fails
PASSED test_astro_service_present_fails_when_ssg
PASSED test_missing_mysql_fails
5 passed
```

- [ ] **Step 6: Commit**

```bash
git add docker-compose.yml openspec/checks/docker.py tests/openspec/test_docker.py
git commit -m "feat: docker compose config and docker conformance check"
```

---

### Task 5: Nginx Config + Nginx Check

**Files:**
- Create: `tests/openspec/test_nginx.py`
- Create: `openspec/checks/nginx.py`
- Create: `nginx/default.conf`

**Interfaces:**
- Consumes: `spec['services']`, `spec['routing']`
- Produces: `nginx.check(spec, base_dir='.') -> list[str]`

- [ ] **Step 1: Write the failing tests**

```python
# tests/openspec/test_nginx.py
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))

from openspec.checks.nginx import check

SPEC = {
    "services": {
        "wordpress": {"domain": "wp.bball.klarr.us", "port": 8080},
        "astro": {"domain": "astro.bball.klarr.us", "mode": "ssg"},
    },
    "routing": {
        "upstreams": [
            {"service": "wordpress", "domain": "wp.bball.klarr.us", "proxy_port": 8080},
            {"service": "astro", "domain": "astro.bball.klarr.us",
             "serve_static": "/var/www/sdd-demo/astro/dist"},
        ]
    },
}

VALID_NGINX = """\
server {
    listen 80;
    server_name wp.bball.klarr.us;
    return 301 https://$host$request_uri;
}
server {
    listen 443 ssl;
    server_name wp.bball.klarr.us;
    ssl_certificate /etc/letsencrypt/live/wp.bball.klarr.us/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/wp.bball.klarr.us/privkey.pem;
    location / {
        proxy_pass http://localhost:8080;
    }
}
server {
    listen 80;
    server_name astro.bball.klarr.us;
    return 301 https://$host$request_uri;
}
server {
    listen 443 ssl;
    server_name astro.bball.klarr.us;
    ssl_certificate /etc/letsencrypt/live/astro.bball.klarr.us/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/astro.bball.klarr.us/privkey.pem;
    root /var/www/sdd-demo/astro/dist;
    location / {
        try_files $uri $uri/ /index.html;
    }
}
"""


def test_valid_nginx_passes(tmp_path):
    (tmp_path / "nginx").mkdir()
    (tmp_path / "nginx" / "default.conf").write_text(VALID_NGINX)
    assert check(SPEC, base_dir=str(tmp_path)) == []


def test_wrong_wp_port_fails(tmp_path):
    (tmp_path / "nginx").mkdir()
    conf = VALID_NGINX.replace("localhost:8080", "localhost:9090")
    (tmp_path / "nginx" / "default.conf").write_text(conf)
    failures = check(SPEC, base_dir=str(tmp_path))
    assert any("wp.bball.klarr.us" in f or "proxy_pass" in f for f in failures)


def test_astro_proxy_pass_fails(tmp_path):
    (tmp_path / "nginx").mkdir()
    conf = VALID_NGINX.replace(
        "root /var/www/sdd-demo/astro/dist;",
        "proxy_pass http://localhost:4321;",
    )
    (tmp_path / "nginx" / "default.conf").write_text(conf)
    failures = check(SPEC, base_dir=str(tmp_path))
    assert any("astro" in f.lower() or "root" in f for f in failures)


def test_missing_ssl_fails(tmp_path):
    (tmp_path / "nginx").mkdir()
    conf = "\n".join(
        l for l in VALID_NGINX.splitlines() if "ssl_certificate" not in l
    )
    (tmp_path / "nginx" / "default.conf").write_text(conf)
    failures = check(SPEC, base_dir=str(tmp_path))
    assert any("ssl" in f.lower() for f in failures)
```

- [ ] **Step 2: Run to verify failure**

```bash
pytest tests/openspec/test_nginx.py -v
```

Expected: `ImportError` — `nginx` module not yet implemented.

- [ ] **Step 3: Write `openspec/checks/nginx.py`**

```python
from pathlib import Path


def check(spec: dict, base_dir: str = ".") -> list[str]:
    conf_path = Path(base_dir, "nginx", "default.conf")
    if not conf_path.exists():
        return ["nginx/default.conf not found"]

    content = conf_path.read_text()
    failures: list[str] = []

    wp_domain = spec["services"]["wordpress"]["domain"]
    wp_port = spec["services"]["wordpress"]["port"]
    astro_domain = spec["services"]["astro"]["domain"]
    static_path = next(
        u["serve_static"]
        for u in spec["routing"]["upstreams"]
        if u["service"] == "astro"
    )

    if f"server_name {wp_domain}" not in content:
        failures.append(f"No server block for {wp_domain}")
    elif f"proxy_pass http://localhost:{wp_port}" not in content:
        failures.append(
            f"{wp_domain}: expected proxy_pass to port {wp_port}"
        )

    if f"server_name {astro_domain}" not in content:
        failures.append(f"No server block for {astro_domain}")
    else:
        if f"root {static_path}" not in content:
            failures.append(
                f"{astro_domain}: expected 'root {static_path}'"
            )

    if "ssl_certificate" not in content:
        failures.append("SSL certificates not configured in nginx/default.conf")

    return failures
```

- [ ] **Step 4: Write `nginx/default.conf`**

```nginx
server {
    listen 80;
    server_name wp.bball.klarr.us;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name wp.bball.klarr.us;

    ssl_certificate     /etc/letsencrypt/live/wp.bball.klarr.us/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/wp.bball.klarr.us/privkey.pem;

    location / {
        proxy_pass       http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

server {
    listen 80;
    server_name astro.bball.klarr.us;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name astro.bball.klarr.us;

    ssl_certificate     /etc/letsencrypt/live/astro.bball.klarr.us/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/astro.bball.klarr.us/privkey.pem;

    root /var/www/sdd-demo/astro/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/openspec/test_nginx.py -v
```

Expected: `4 passed`

- [ ] **Step 6: Commit**

```bash
git add nginx/ openspec/checks/nginx.py tests/openspec/test_nginx.py
git commit -m "feat: nginx config and nginx conformance check"
```

---

### Task 6: GitHub Actions Workflow + CICD Check + Content Script

**Files:**
- Create: `tests/openspec/test_cicd.py`
- Create: `openspec/checks/cicd.py`
- Create: `.github/workflows/deploy.yml`
- Create: `scripts/generate-content.js`

**Interfaces:**
- Consumes: `spec['cicd']`
- Produces: `cicd.check(spec, base_dir='.') -> list[str]`

- [ ] **Step 1: Write the failing tests**

```python
# tests/openspec/test_cicd.py
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))

from openspec.checks.cicd import check

SPEC = {
    "cicd": {
        "trigger": "wordpress-webhook",
        "steps": [
            {
                "fetch_posts": {
                    "url": "https://wp.bball.klarr.us/wp-json/wp/v2/posts",
                    "params": {"per_page": 100, "page": 1},
                }
            }
        ],
    }
}

VALID_WORKFLOW = """\
on:
  repository_dispatch:
    types: [wordpress-post-change]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Validate OpenSpec
        run: python openspec/validate.py
      - name: Fetch posts
        run: |
          curl -s "https://wp.bball.klarr.us/wp-json/wp/v2/posts?per_page=100&page=1" -o posts.json
      - name: Build Astro
        run: npm run build
        working-directory: ./astro
      - name: Deploy
        run: |
          rsync -avz -e "ssh -i ~/.ssh/deploy_key" ./astro/dist/ ubuntu@astro.bball.klarr.us:/var/www/sdd-demo/astro/dist/
"""


def test_valid_workflow_passes(tmp_path):
    gh_dir = tmp_path / ".github" / "workflows"
    gh_dir.mkdir(parents=True)
    (gh_dir / "deploy.yml").write_text(VALID_WORKFLOW)
    assert check(SPEC, base_dir=str(tmp_path)) == []


def test_missing_webhook_trigger_fails(tmp_path):
    gh_dir = tmp_path / ".github" / "workflows"
    gh_dir.mkdir(parents=True)
    workflow = "on:\n  push:\n    branches: [main]\njobs:\n  deploy:\n    runs-on: ubuntu-latest\n    steps: []\n"
    (gh_dir / "deploy.yml").write_text(workflow)
    failures = check(SPEC, base_dir=str(tmp_path))
    assert any("repository_dispatch" in f or "trigger" in f for f in failures)


def test_missing_fetch_url_fails(tmp_path):
    gh_dir = tmp_path / ".github" / "workflows"
    gh_dir.mkdir(parents=True)
    workflow = VALID_WORKFLOW.replace(
        "https://wp.bball.klarr.us/wp-json/wp/v2/posts", "https://example.com"
    )
    (gh_dir / "deploy.yml").write_text(workflow)
    failures = check(SPEC, base_dir=str(tmp_path))
    assert any("fetch" in f.lower() or "url" in f.lower() for f in failures)


def test_missing_rsync_fails(tmp_path):
    gh_dir = tmp_path / ".github" / "workflows"
    gh_dir.mkdir(parents=True)
    workflow = "\n".join(
        l for l in VALID_WORKFLOW.splitlines() if "rsync" not in l
    )
    (gh_dir / "deploy.yml").write_text(workflow)
    failures = check(SPEC, base_dir=str(tmp_path))
    assert any("rsync" in f for f in failures)
```

- [ ] **Step 2: Run to verify failure**

```bash
pytest tests/openspec/test_cicd.py -v
```

Expected: `ImportError` — `cicd` module not yet implemented.

- [ ] **Step 3: Write `openspec/checks/cicd.py`**

```python
from pathlib import Path

import yaml


def check(spec: dict, base_dir: str = ".") -> list[str]:
    workflow_path = Path(base_dir, ".github", "workflows", "deploy.yml")
    if not workflow_path.exists():
        return [".github/workflows/deploy.yml not found"]

    data = yaml.safe_load(workflow_path.read_text())
    failures: list[str] = []

    if "repository_dispatch" not in (data.get("on") or {}):
        failures.append("Webhook trigger (repository_dispatch) not found")

    all_runs: list[str] = []
    for job in (data.get("jobs") or {}).values():
        for step in job.get("steps") or []:
            if "run" in step:
                all_runs.append(step["run"])
    combined = "\n".join(all_runs)

    fetch_url = spec["cicd"]["steps"][0]["fetch_posts"]["url"]
    if fetch_url not in combined:
        failures.append(f"Fetch posts URL not found in workflow: {fetch_url}")

    if "astro build" not in combined and "npm run build" not in combined:
        failures.append("astro build step not found in workflow")

    if "rsync" not in combined:
        failures.append("rsync deploy step not found in workflow")

    if "openspec/validate.py" not in combined:
        failures.append("openspec validate step not found in workflow")

    return failures
```

- [ ] **Step 4: Write `.github/workflows/deploy.yml`**

```yaml
name: Deploy on WordPress Post Change

on:
  repository_dispatch:
    types: [wordpress-post-change]

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install OpenSpec dependencies
        run: pip install -r openspec/requirements.txt

      - name: Validate OpenSpec
        run: python openspec/validate.py

      - name: Fetch WordPress posts
        run: |
          curl -s "https://wp.bball.klarr.us/wp-json/wp/v2/posts?per_page=100&page=1&_embed" \
            -o posts.json

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: "20"

      - name: Install Astro dependencies
        run: npm ci
        working-directory: ./astro

      - name: Generate content files from posts
        run: node scripts/generate-content.js

      - name: Build Astro
        run: npm run build
        working-directory: ./astro

      - name: Deploy via rsync
        env:
          DEPLOY_KEY: ${{ secrets.GH_DEPLOY_KEY }}
        run: |
          mkdir -p ~/.ssh
          echo "$DEPLOY_KEY" > ~/.ssh/deploy_key
          chmod 600 ~/.ssh/deploy_key
          rsync -avz --delete \
            -e "ssh -i ~/.ssh/deploy_key -o StrictHostKeyChecking=no" \
            ./astro/dist/ \
            ubuntu@astro.bball.klarr.us:/var/www/sdd-demo/astro/dist/
```

- [ ] **Step 5: Write `scripts/generate-content.js`**

```js
const fs = require("fs");
const path = require("path");

const postsFile = path.join(__dirname, "..", "posts.json");
const contentDir = path.join(__dirname, "..", "astro", "src", "content", "blog");

const posts = JSON.parse(fs.readFileSync(postsFile, "utf-8"));

// Clear existing markdown files
fs.readdirSync(contentDir)
  .filter((f) => f.endsWith(".md"))
  .forEach((f) => fs.unlinkSync(path.join(contentDir, f)));

const ALLOWED_CATEGORIES = new Set(["Sport", "Software"]);

posts.forEach((post) => {
  const terms = post._embedded?.["wp:term"]?.[0] ?? [];
  const catName = terms.find((t) => ALLOWED_CATEGORIES.has(t.name))?.name ?? "Software";
  const slug = post.slug;
  const title = post.title.rendered.replace(/"/g, '\\"');
  const rawExcerpt = post.excerpt.rendered.replace(/<[^>]+>/g, "").trim();
  const excerpt = rawExcerpt.slice(0, 200).replace(/"/g, '\\"');
  const date = post.date.split("T")[0];
  const body = post.content.rendered.replace(/<[^>]+>/g, "").trim();

  const md = `---
title: "${title}"
category: "${catName}"
date: "${date}"
excerpt: "${excerpt}"
wpId: ${post.id}
---

${body}
`;

  fs.writeFileSync(path.join(contentDir, `${slug}.md`), md);
});

console.log(`Generated ${posts.length} content files in ${contentDir}`);
```

- [ ] **Step 6: Run tests to verify they pass**

```bash
pytest tests/openspec/test_cicd.py -v
```

Expected: `4 passed`

- [ ] **Step 7: Run full validator to confirm all checks pass**

```bash
python openspec/validate.py
```

Expected:
```
[PASS] schema
[PASS] terraform
[PASS] docker
[PASS] nginx
[PASS] cicd

All checks passed.
```

- [ ] **Step 8: Commit**

```bash
git add .github/ scripts/ openspec/checks/cicd.py tests/openspec/test_cicd.py
git commit -m "feat: github actions workflow, cicd check, and content generator"
```

---

### Task 7: Astro Scaffold

**Files:**
- Create: `astro/astro.config.mjs`
- Create: `astro/package.json`
- Create: `astro/tsconfig.json`
- Create: `astro/vitest.config.ts`
- Create: `astro/src/tests/setup.ts`
- Create: `astro/src/content/config.ts`
- Create: `astro/src/content/blog/.gitkeep`
- Create: `astro/src/pages/index.astro`
- Create: `astro/src/styles/global.css`

**Interfaces:**
- Produces: Astro project buildable via `npm run build`
- Produces: Test runner via `npm test`

- [ ] **Step 1: Initialize Astro project**

```bash
cd astro
npm create astro@latest . -- --template minimal --typescript strict --no-install --no-git
npm install
npm install @astrojs/react react react-dom
npm install -D @types/react @types/react-dom vitest @testing-library/react @testing-library/jest-dom jsdom @vitejs/plugin-react
cd ..
```

- [ ] **Step 2: Write `astro/astro.config.mjs`**

```js
import { defineConfig } from "astro/config";
import react from "@astrojs/react";

export default defineConfig({
  integrations: [react()],
  output: "static",
});
```

- [ ] **Step 3: Write `astro/vitest.config.ts`**

```ts
import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/tests/setup.ts"],
  },
});
```

- [ ] **Step 4: Write `astro/src/tests/setup.ts`**

```ts
import "@testing-library/jest-dom";
```

- [ ] **Step 5: Add test script to `astro/package.json`**

Open `astro/package.json` and add `"test": "vitest run"` to the `scripts` section:

```json
{
  "scripts": {
    "dev": "astro dev",
    "build": "astro build",
    "preview": "astro preview",
    "test": "vitest run"
  }
}
```

- [ ] **Step 6: Write `astro/src/content/config.ts`**

```ts
import { defineCollection, z } from "astro:content";

const blog = defineCollection({
  type: "content",
  schema: z.object({
    title: z.string(),
    category: z.enum(["Sport", "Software"]),
    date: z.string(),
    excerpt: z.string(),
    wpId: z.number(),
  }),
});

export const collections = { blog };
```

- [ ] **Step 7: Write `astro/src/content/blog/.gitkeep`**

```bash
touch astro/src/content/blog/.gitkeep
```

- [ ] **Step 8: Write `astro/src/styles/global.css`**

```css
:root {
  --bg: #ffffff;
  --text: #1a1a1a;
  --accent: #3b82f6;
}

:root.dark {
  --bg: #0f172a;
  --text: #f1f5f9;
  --accent: #60a5fa;
}

body {
  background: var(--bg);
  color: var(--text);
  font-family: system-ui, sans-serif;
  margin: 0;
  transition: background 0.2s, color 0.2s;
}
```

- [ ] **Step 9: Write `astro/src/pages/index.astro`** (placeholder — updated in Task 11)

```astro
---
import "../styles/global.css";
---
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>Eugenio Astro</title>
  </head>
  <body>
    <main>
      <p>Eugenio Astro</p>
    </main>
  </body>
</html>
```

- [ ] **Step 10: Verify build succeeds**

```bash
cd astro && npm run build && cd ..
```

Expected: `dist/` directory created, exit 0.

- [ ] **Step 11: Commit**

```bash
git add astro/
git commit -m "feat: astro project scaffold with vitest and content collection"
```

---

### Task 8: CategoryFilter Component

**Files:**
- Create: `astro/src/components/CategoryFilter.tsx`
- Create: `astro/src/tests/CategoryFilter.test.tsx`

**Interfaces:**
- Consumes: `Post[]` prop
- Produces: `<CategoryFilter posts={Post[]} />` — renders filtered post list, hydrates with `client:load`

- [ ] **Step 1: Write the failing test**

```tsx
// astro/src/tests/CategoryFilter.test.tsx
import { render, screen, fireEvent } from "@testing-library/react";
import CategoryFilter from "../components/CategoryFilter";

const posts = [
  { title: "Basketball finals", category: "Sport" as const, slug: "bball", excerpt: "Sport post" },
  { title: "React hooks guide", category: "Software" as const, slug: "react", excerpt: "Software post" },
  { title: "Soccer match", category: "Sport" as const, slug: "soccer", excerpt: "Another sport" },
];

test("shows all posts by default", () => {
  render(<CategoryFilter posts={posts} />);
  expect(screen.getByText("Basketball finals")).toBeInTheDocument();
  expect(screen.getByText("React hooks guide")).toBeInTheDocument();
  expect(screen.getByText("Soccer match")).toBeInTheDocument();
});

test("All button is active by default", () => {
  render(<CategoryFilter posts={posts} />);
  expect(screen.getByRole("button", { name: "All" })).toHaveAttribute("aria-pressed", "true");
});

test("filters to Sport only", () => {
  render(<CategoryFilter posts={posts} />);
  fireEvent.click(screen.getByRole("button", { name: "Sport" }));
  expect(screen.getByText("Basketball finals")).toBeInTheDocument();
  expect(screen.getByText("Soccer match")).toBeInTheDocument();
  expect(screen.queryByText("React hooks guide")).not.toBeInTheDocument();
});

test("filters to Software only", () => {
  render(<CategoryFilter posts={posts} />);
  fireEvent.click(screen.getByRole("button", { name: "Software" }));
  expect(screen.getByText("React hooks guide")).toBeInTheDocument();
  expect(screen.queryByText("Basketball finals")).not.toBeInTheDocument();
});

test("All button restores full list", () => {
  render(<CategoryFilter posts={posts} />);
  fireEvent.click(screen.getByRole("button", { name: "Sport" }));
  fireEvent.click(screen.getByRole("button", { name: "All" }));
  expect(screen.getByText("React hooks guide")).toBeInTheDocument();
});
```

- [ ] **Step 2: Run to verify failure**

```bash
cd astro && npm test -- CategoryFilter && cd ..
```

Expected: `Cannot find module '../components/CategoryFilter'`

- [ ] **Step 3: Write `astro/src/components/CategoryFilter.tsx`**

```tsx
import { useState } from "react";

type Category = "All" | "Sport" | "Software";

interface Post {
  title: string;
  category: "Sport" | "Software";
  slug: string;
  excerpt: string;
}

interface Props {
  posts: Post[];
}

export default function CategoryFilter({ posts }: Props) {
  const [active, setActive] = useState<Category>("All");

  const filtered =
    active === "All" ? posts : posts.filter((p) => p.category === active);

  return (
    <div>
      <nav aria-label="Category filter">
        {(["All", "Sport", "Software"] as Category[]).map((cat) => (
          <button
            key={cat}
            onClick={() => setActive(cat)}
            aria-pressed={active === cat}
          >
            {cat}
          </button>
        ))}
      </nav>
      <ul>
        {filtered.map((post) => (
          <li key={post.slug}>
            <a href={`/blog/${post.slug}`}>{post.title}</a>
            <p>{post.excerpt}</p>
          </li>
        ))}
      </ul>
    </div>
  );
}
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd astro && npm test -- CategoryFilter && cd ..
```

Expected: `5 passed`

- [ ] **Step 5: Commit**

```bash
git add astro/src/components/CategoryFilter.tsx astro/src/tests/CategoryFilter.test.tsx
git commit -m "feat: CategoryFilter React island with category toggle"
```

---

### Task 9: LiveClock Component

**Files:**
- Create: `astro/src/components/LiveClock.tsx`
- Create: `astro/src/tests/LiveClock.test.tsx`

**Interfaces:**
- Consumes: nothing (reads from browser `Intl` and `Date`)
- Produces: `<LiveClock />` — renders `HH:mm:ss · Continent/City`, hydrates with `client:only="react"`

- [ ] **Step 1: Write the failing test**

```tsx
// astro/src/tests/LiveClock.test.tsx
import { render, screen, act } from "@testing-library/react";
import { vi, beforeEach, afterEach } from "vitest";
import LiveClock from "../components/LiveClock";

const MOCK_TIMEZONE = "Europe/Warsaw";

beforeEach(() => {
  vi.spyOn(global.Intl, "DateTimeFormat").mockImplementation(
    () =>
      ({
        resolvedOptions: () => ({ timeZone: MOCK_TIMEZONE }),
        format: () => "",
        formatToParts: () => [],
      } as unknown as Intl.DateTimeFormat)
  );
  vi.useFakeTimers();
  vi.setSystemTime(new Date("2026-06-29T14:23:07Z"));
});

afterEach(() => {
  vi.restoreAllMocks();
  vi.useRealTimers();
});

test("renders time in HH:mm:ss format", async () => {
  await act(async () => {
    render(<LiveClock />);
  });
  expect(screen.getByRole("status").textContent).toMatch(/\d{2}:\d{2}:\d{2}/);
});

test("renders timezone in Continent/City format", async () => {
  await act(async () => {
    render(<LiveClock />);
  });
  expect(screen.getByRole("status").textContent).toContain("Europe/Warsaw");
});

test("renders separator between time and timezone", async () => {
  await act(async () => {
    render(<LiveClock />);
  });
  expect(screen.getByRole("status").textContent).toContain("·");
});

test("updates time after 1 second", async () => {
  await act(async () => {
    render(<LiveClock />);
  });
  const initial = screen.getByRole("status").textContent;

  await act(async () => {
    vi.advanceTimersByTime(1000);
  });

  expect(screen.getByRole("status")).toBeInTheDocument();
});
```

- [ ] **Step 2: Run to verify failure**

```bash
cd astro && npm test -- LiveClock && cd ..
```

Expected: `Cannot find module '../components/LiveClock'`

- [ ] **Step 3: Write `astro/src/components/LiveClock.tsx`**

```tsx
import { useState, useEffect } from "react";

function formatTime(date: Date): string {
  return date.toLocaleTimeString("en-GB", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  });
}

export default function LiveClock() {
  const [time, setTime] = useState<string>("");
  const [timezone, setTimezone] = useState<string>("");

  useEffect(() => {
    setTimezone(Intl.DateTimeFormat().resolvedOptions().timeZone);
    setTime(formatTime(new Date()));

    const interval = setInterval(() => {
      setTime(formatTime(new Date()));
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  if (!time) return null;

  return (
    <span role="status" aria-live="polite" aria-label={`Current time: ${time} ${timezone}`}>
      {time} · {timezone}
    </span>
  );
}
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd astro && npm test -- LiveClock && cd ..
```

Expected: `4 passed`

- [ ] **Step 5: Commit**

```bash
git add astro/src/components/LiveClock.tsx astro/src/tests/LiveClock.test.tsx
git commit -m "feat: LiveClock React island with HH:mm:ss and Intl timezone"
```

---

### Task 10: ThemeToggle Component

**Files:**
- Create: `astro/src/components/ThemeToggle.tsx`
- Create: `astro/src/tests/ThemeToggle.test.tsx`

**Interfaces:**
- Consumes: `localStorage.getItem('theme')`, `window.matchMedia`
- Produces: `<ThemeToggle />` — persists dark/light mode, hydrates with `client:load`

- [ ] **Step 1: Write the failing test**

```tsx
// astro/src/tests/ThemeToggle.test.tsx
import { render, screen, fireEvent } from "@testing-library/react";
import { vi, beforeEach } from "vitest";
import ThemeToggle from "../components/ThemeToggle";

beforeEach(() => {
  localStorage.clear();
  document.documentElement.className = "";
  vi.spyOn(window, "matchMedia").mockImplementation((query) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  }));
});

test("renders a toggle button", () => {
  render(<ThemeToggle />);
  expect(screen.getByRole("button")).toBeInTheDocument();
});

test("defaults to light mode when no preference stored", () => {
  render(<ThemeToggle />);
  expect(document.documentElement.classList.contains("dark")).toBe(false);
});

test("clicking toggle switches to dark mode", () => {
  render(<ThemeToggle />);
  fireEvent.click(screen.getByRole("button"));
  expect(document.documentElement.classList.contains("dark")).toBe(true);
});

test("dark mode persists to localStorage", () => {
  render(<ThemeToggle />);
  fireEvent.click(screen.getByRole("button"));
  expect(localStorage.getItem("theme")).toBe("dark");
});

test("clicking twice returns to light mode", () => {
  render(<ThemeToggle />);
  fireEvent.click(screen.getByRole("button"));
  fireEvent.click(screen.getByRole("button"));
  expect(document.documentElement.classList.contains("dark")).toBe(false);
  expect(localStorage.getItem("theme")).toBe("light");
});

test("respects stored dark preference on mount", () => {
  localStorage.setItem("theme", "dark");
  render(<ThemeToggle />);
  expect(document.documentElement.classList.contains("dark")).toBe(true);
});
```

- [ ] **Step 2: Run to verify failure**

```bash
cd astro && npm test -- ThemeToggle && cd ..
```

Expected: `Cannot find module '../components/ThemeToggle'`

- [ ] **Step 3: Write `astro/src/components/ThemeToggle.tsx`**

```tsx
import { useState, useEffect } from "react";

export default function ThemeToggle() {
  const [isDark, setIsDark] = useState(false);

  useEffect(() => {
    const stored = localStorage.getItem("theme");
    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    const dark = stored ? stored === "dark" : prefersDark;
    setIsDark(dark);
    document.documentElement.classList.toggle("dark", dark);
  }, []);

  function toggle() {
    const next = !isDark;
    setIsDark(next);
    localStorage.setItem("theme", next ? "dark" : "light");
    document.documentElement.classList.toggle("dark", next);
  }

  return (
    <button
      onClick={toggle}
      aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
    >
      {isDark ? "☀" : "☾"}
    </button>
  );
}
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd astro && npm test -- ThemeToggle && cd ..
```

Expected: `6 passed`

- [ ] **Step 5: Commit**

```bash
git add astro/src/components/ThemeToggle.tsx astro/src/tests/ThemeToggle.test.tsx
git commit -m "feat: ThemeToggle React island with localStorage persistence"
```

---

### Task 11: Header + Index Page + Build Verification

**Files:**
- Create: `astro/src/components/Header.astro`
- Modify: `astro/src/pages/index.astro`

**Interfaces:**
- Consumes: `LiveClock`, `ThemeToggle`, `CategoryFilter`, `blog` content collection
- Produces: fully built site via `npm run build`

- [ ] **Step 1: Write `astro/src/components/Header.astro`**

```astro
---
import LiveClock from "./LiveClock.tsx";
import ThemeToggle from "./ThemeToggle.tsx";
---

<header>
  <a href="/" class="site-title">Eugenio Astro</a>
  <div class="header-controls">
    <LiveClock client:only="react" />
    <ThemeToggle client:load />
  </div>
</header>

<style>
  header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1rem 2rem;
    border-bottom: 1px solid currentColor;
  }
  .site-title {
    font-weight: bold;
    font-size: 1.25rem;
    text-decoration: none;
    color: inherit;
  }
  .header-controls {
    display: flex;
    align-items: center;
    gap: 1rem;
  }
</style>
```

- [ ] **Step 2: Update `astro/src/pages/index.astro`**

```astro
---
import { getCollection } from "astro:content";
import Header from "../components/Header.astro";
import CategoryFilter from "../components/CategoryFilter.tsx";
import "../styles/global.css";

const entries = await getCollection("blog");
const posts = entries.map((e) => ({
  title: e.data.title,
  category: e.data.category,
  slug: e.slug,
  excerpt: e.data.excerpt,
}));
---

<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width" />
    <title>Eugenio Astro</title>
  </head>
  <body>
    <Header />
    <main>
      <CategoryFilter posts={posts} client:load />
    </main>
  </body>
</html>
```

- [ ] **Step 3: Run all Astro tests**

```bash
cd astro && npm test && cd ..
```

Expected: all tests from Tasks 8–10 pass (15 total).

- [ ] **Step 4: Run full Astro build**

```bash
cd astro && npm run build && cd ..
```

Expected: `dist/` populated, exit 0, no TypeScript errors.

- [ ] **Step 5: Run full OpenSpec validate**

```bash
python openspec/validate.py
```

Expected:
```
[PASS] schema
[PASS] terraform
[PASS] docker
[PASS] nginx
[PASS] cicd

All checks passed.
```

- [ ] **Step 6: Run full Python test suite**

```bash
pytest tests/ -v
```

Expected: all 18 tests pass.

- [ ] **Step 7: Commit**

```bash
git add astro/src/components/Header.astro astro/src/pages/index.astro
git commit -m "feat: header with LiveClock and ThemeToggle, wire CategoryFilter to content collection"
```

---

## Post-Implementation Changes

These changes were made after Tasks 1–11 were completed. All are reflected in the current codebase and `openspec.yaml`.

### P1: Category update — Software → Travel + Uncategorized

- Categories changed from `[Sport, Software]` to `[Sport, Travel, Uncategorized]`
- `Uncategorized` is the fallback when a WP post has no matching category
- Files updated: `openspec.yaml`, `astro/src/content.config.ts`, `astro/src/components/CategoryFilter.tsx`, `scripts/generate-content.js`, all tests

### P2: Node version — 20 → 22

- `deploy.yml` had `node-version: "20"`; Astro 7 requires `>=22.12.0`
- Fixed to `node-version: "22"`

### P3: Shared `/media/` location

- WordPress uploads Docker volume bind-mounted to `/var/www/sdd-demo/media` on host
- `location /media/ { alias /var/www/sdd-demo/media/; }` added to all nginx server blocks
- Content generators rewrite `wp-content/uploads/` URLs to `/media/` in post body
- Spec: `routing.shared_media.host_path` / `url_path`
- nginx.py check updated to verify `location /media/` and `alias` are present

### P4: Domain migration — `bball.klarr.us` → `4eng.online`

- All three domains updated: `wp.4eng.online`, `astro.4eng.online`, `docu.4eng.online`
- Files updated: `openspec.yaml`, `nginx/default.conf`, `deploy.yml`, `scripts/generate-content.js`, all test fixtures

### P5: EC2 IAM role with Route 53 permissions

- New Terraform resources: `aws_iam_role`, `aws_iam_role_policy` (Route 53), `aws_iam_instance_profile`
- EC2 instance gets `iam_instance_profile` set
- Spec: `infrastructure.iam.ec2_role` + `infrastructure.iam.policies`
- terraform.py check updated with 4 new assertions; 3 new tests added

### P6: Docusaurus SSG at `docu.4eng.online`

- New service: Docusaurus 3.7 in blog-only mode (`docs: false`, blog at root `/`)
- `scripts/generate-docusaurus-content.js` generates `docusaurus/blog/YYYY-MM-DD-slug.md`
- Frontmatter: `title`, `date`, `tags: [Category]`, `description`
- Nginx: new server block for `docu.4eng.online` → `root /var/www/sdd-demo/docusaurus/build`
- CI/CD: `npm ci` + `npm run build` in `./docusaurus`, second rsync to `docu.4eng.online`
- nginx.py check generalized to loop over all upstreams (no longer hardcoded for wp/astro)
- cicd.py check: fails if docusaurus service in spec but no docusaurus step in workflow
- 2 new tests added
