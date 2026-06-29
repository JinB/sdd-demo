# Eugenio SDD Demo — Design Spec

**Date:** 2026-06-29  
**Approach:** OpenSpec Spec-Anchored  
**Status:** Approved

---

## 1. Overview

A WordPress/Astro demo managed by OpenSpec using a Spec-Anchored development flow. A single `openspec.yaml` is the source of truth; all implementation files (Terraform, Docker Compose, Nginx, GitHub Actions) must conform to it. A validator CLI enforces conformance locally and as a CI gate.

---

## 2. openspec.yaml

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
    port: 4321            # dev only; prod = static files served by nginx
    domain: astro.bball.klarr.us
    mode: ssg
    features:
      dark_light_switcher: true
      live_clock:
        format: HH:mm:ss
        timezone: Intl    # derived from browser via Intl.DateTimeFormat
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
      serve_static: /var/www/sdd-demo/astro/dist   # absolute path on EC2

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

---

## 3. File Layout

```
sdd-demo/
│
├── openspec.yaml                  ← only file you edit for config
│
├── openspec/
│   ├── validate.py                ← CLI: python openspec/validate.py
│   ├── schema/
│   │   └── openspec.schema.json   ← JSON Schema for the spec
│   └── checks/
│       ├── terraform.py
│       ├── docker.py
│       ├── nginx.py
│       └── cicd.py
│
├── terraform/
│   ├── main.tf
│   ├── variables.tf
│   └── outputs.tf
│
├── docker-compose.yml
│
├── nginx/
│   └── default.conf
│
├── .github/
│   └── workflows/
│       └── deploy.yml
│
└── astro/
    ├── src/
    │   ├── content/blog/          ← replaced by CI/CD on every deploy
    │   └── components/
    │       ├── CategoryFilter.tsx ← React island: All / Sport / Software
    │       ├── LiveClock.tsx      ← React island: HH:mm:ss · Continent/City
    │       ├── ThemeToggle.tsx    ← React island: dark/light switcher
    │       └── Header.astro       ← hosts LiveClock + ThemeToggle
    ├── astro.config.mjs
    └── package.json
```

---

## 4. Infrastructure

**EC2**
- Region: `eu-central-1`
- OS: Ubuntu 24.04
- Instance type: `t3.small` (2 vCPU, 2 GB RAM)
- Security group `sg-spec-demo`: inbound 22/80/443 from all; outbound unrestricted

**Stack on EC2**
- Nginx on host (80/443) — reverse proxy + static file server
- Docker Compose manages: WordPress (port 8080), MySQL (internal only)
- Astro is build-only — no container in production; `astro/dist` served directly by Nginx
- Let's Encrypt SSL via Certbot with auto-renewal cron

**Secrets**
- AWS Secrets Manager stores: `db_password`, `wp_admin_password`, `gh_deploy_key`
- Docker Compose reads DB credentials via environment at startup

---

## 5. Services

### WordPress (Backend)
- Title: Eugenio WP
- Docker container on port 8080
- Categories: Sport, Software
- Public URL: `https://wp.bball.klarr.us`
- REST API endpoint used by CI/CD: `/wp-json/wp/v2/posts?per_page=100&page=1`
- Sends webhook on post change → triggers GitHub Actions

### MySQL
- Docker container, internal network only
- Persistent Docker volume for data
- Password from AWS Secrets Manager (`db_password`)

### Astro (Frontend)
- Title: Eugenio Astro
- Mode: SSG — built to static files, no runtime container
- Public URL: `https://astro.bball.klarr.us`
- Nginx serves `./astro/dist` as static files

---

## 6. Astro Frontend

### CategoryFilter (React Island)
- `client:load` hydration
- Toggle bar: **All** | **Sport** | **Software**
- Filters displayed posts client-side, no page reload

### LiveClock (React Island)
- `client:only="react"` — requires browser APIs, no SSR
- Updates every 1 second via `setInterval`
- Time format: `HH:mm:ss`
- Timezone: `Intl.DateTimeFormat().resolvedOptions().timeZone` → `Continent/City` (e.g. `Europe/Warsaw`)
- Renders as: `14:23:07 · Europe/Warsaw`
- Placed in `Header.astro` alongside the dark/light switcher

### ThemeToggle (React Island)
- `client:load` hydration
- Toggles dark/light mode, always visible regardless of page or category
- Persists preference via `localStorage`

### Header
- Always visible
- Contains: `LiveClock` and `ThemeToggle`, both always rendered
- Implemented in `Header.astro` using Astro's component composition

---

## 7. Routing (Nginx)

```
wp.bball.klarr.us    → proxy_pass to localhost:8080           (WordPress container)
astro.bball.klarr.us → root /var/www/sdd-demo/astro/dist  (static files, no proxy)
```

Both domains: HTTPS enforced, HTTP redirects to HTTPS, Let's Encrypt certificates.

---

## 8. CI/CD (GitHub Actions)

**Trigger:** WordPress webhook on post create/update/delete → `repository_dispatch` event to GitHub Actions.

**Pipeline steps:**
1. `openspec validate` — abort if spec and implementation have drifted
2. Fetch all posts from `https://wp.bball.klarr.us/wp-json/wp/v2/posts?per_page=100&page=1`
3. Write posts as content files into `./astro/src/content/blog` (replaces all existing)
4. Run `astro build` → outputs to `./astro/dist`
5. rsync built files to EC2 over SSH using `gh_deploy_key` from GitHub Secrets

---

## 9. OpenSpec Validator

**Entry point:** `python openspec/validate.py`

**Pass 1 — Schema validation**  
Validates `openspec.yaml` against `openspec.schema.json`. Catches missing required fields and invalid values.

**Pass 2 — Conformance checks**

| Module | Asserts |
|---|---|
| `terraform.py` | region, instance_type, SG name, inbound ports [22,80,443], Secrets Manager resources for all `secrets.keys` |
| `docker.py` | WordPress on port 8080, MySQL present, **no Astro service** (spec says `mode: ssg`), shared network |
| `nginx.py` | WordPress upstream uses `proxy_pass :8080`, Astro upstream uses `root` directive (not `proxy_pass`), SSL blocks present for both domains |
| `cicd.py` | Webhook trigger present, fetch URL matches spec, `astro build` step present, rsync-SSH deploy step present |

**Output:**
```
[PASS] schema
[PASS] terraform
[FAIL] nginx
       → astro.bball.klarr.us: expected root directive, found proxy_pass :4321
[PASS] docker
[PASS] cicd

1 check failed.
```

**CI gate:** `deploy.yml` runs `openspec validate` as its first step. Deploy is blocked on any failure.

---

## 10. Key Constraints

- Astro runs in SSG mode — no Astro container in production
- Nginx serves Astro dist files directly (not proxied)
- `openspec validate` must pass before any deploy
- All secrets stored in AWS Secrets Manager — no plaintext credentials in any file
- t3.small is sized for demo load only
