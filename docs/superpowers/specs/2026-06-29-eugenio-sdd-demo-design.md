# Eugenio SDD Demo — Design Spec

**Date:** 2026-06-29  
**Last updated:** 2026-06-30  
**Approach:** OpenSpec Spec-Anchored  
**Status:** Approved — implemented and live

---

## 1. Overview

A WordPress/Astro/Docusaurus demo managed by OpenSpec using a Spec-Anchored development flow. A single `openspec.yaml` is the source of truth; all implementation files (Terraform, Docker Compose, Nginx, GitHub Actions) must conform to it. A validator CLI enforces conformance locally and as a CI gate.

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
  iam:
    ec2_role: sdd-demo-ec2-role
    policies:
      - route53_update

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
    domain: wp.4eng.online
    categories: [Sport, Travel, Uncategorized]

  mysql:
    image: mysql:8.0
    secret_ref: db_password

  astro:
    title: Eugenio Astro
    port: 4321            # dev only; prod = static files served by nginx
    domain: astro.4eng.online
    mode: ssg
    features:
      dark_light_switcher: true
      live_clock:
        format: HH:mm:ss
        timezone: Intl    # derived from browser via Intl.DateTimeFormat
    categories: [Sport, Travel, Uncategorized]

  docusaurus:
    title: Eugenio Docu
    port: 3000            # dev only; prod = static files served by nginx
    domain: docu.4eng.online
    mode: ssg
    build_output: build

routing:
  engine: nginx
  ssl: letsencrypt
  shared_media:
    host_path: /var/www/sdd-demo/media
    url_path: /media
  upstreams:
    - service: wordpress
      domain: wp.4eng.online
      proxy_port: 8080
    - service: astro
      domain: astro.4eng.online
      serve_static: /var/www/sdd-demo/astro/dist
    - service: docusaurus
      domain: docu.4eng.online
      serve_static: /var/www/sdd-demo/docusaurus/build

cicd:
  provider: github-actions
  trigger: wordpress-webhook
  steps:
    - fetch_posts:
        url: "https://wp.4eng.online/wp-json/wp/v2/posts"
        params: { per_page: 100, page: 1 }
    - build_astro:
        replaces: ./astro/src/content/blog
    - build_docusaurus:
        replaces: ./docusaurus/blog
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
├── tests/openspec/
│   ├── test_validate.py
│   ├── test_terraform.py
│   ├── test_docker.py
│   ├── test_nginx.py
│   └── test_cicd.py
│
├── terraform/
│   ├── main.tf
│   └── variables.tf
│
├── docker-compose.yml
│
├── nginx/
│   └── default.conf
│
├── scripts/
│   ├── generate-content.js            ← WP posts → astro/src/content/blog/
│   └── generate-docusaurus-content.js ← WP posts → docusaurus/blog/
│
├── .github/
│   └── workflows/
│       └── deploy.yml
│
├── astro/
│   ├── src/
│   │   ├── content/
│   │   │   ├── config.ts
│   │   │   └── blog/              ← replaced by CI/CD on every deploy
│   │   ├── components/
│   │   │   ├── CategoryFilter.tsx ← React island: All / Sport / Travel / Uncategorized
│   │   │   ├── LiveClock.tsx      ← React island: HH:mm:ss · Continent/City
│   │   │   ├── ThemeToggle.tsx    ← React island: dark/light switcher
│   │   │   └── Header.astro       ← hosts LiveClock + ThemeToggle
│   │   └── pages/index.astro
│   ├── astro.config.mjs
│   └── package.json
│
└── docusaurus/
    ├── docusaurus.config.js       ← blog-only mode, root path /
    ├── package.json
    ├── blog/                      ← replaced by CI/CD on every deploy
    └── src/css/custom.css
```

---

## 4. Infrastructure

**EC2**
- Region: `eu-central-1`
- OS: Ubuntu 24.04
- Instance type: `t3.small` (2 vCPU, 2 GB RAM)
- Security group `sg-spec-demo`: inbound 22/80/443 from all; outbound unrestricted

**IAM**
- Role: `sdd-demo-ec2-role` — attached to the EC2 instance via instance profile
- Inline policy `route53_update`: allows `route53:ChangeResourceRecordSets`, `GetChange`, `ListHostedZones`, `ListResourceRecordSets`
- Purpose: enables Certbot DNS-01 challenge and programmatic Route 53 updates from the instance

**Stack on EC2**
- Nginx on host (80/443) — reverse proxy + static file server
- Docker Compose manages: WordPress (port 8080), MySQL (internal only)
- WordPress uploads mounted to host at `/var/www/sdd-demo/media` (bind mount)
- Astro and Docusaurus are build-only — no containers in production; built static files served directly by Nginx
- Let's Encrypt SSL via Certbot with auto-renewal cron

**Secrets**
- AWS Secrets Manager stores: `db_password`, `wp_admin_password`, `gh_deploy_key`
- Docker Compose reads DB credentials via environment at startup

---

## 5. Services

### WordPress (Backend)
- Title: Eugenio WP
- Docker container on port 8080
- Categories: Sport, Travel, Uncategorized
- Public URL: `https://wp.4eng.online`
- REST API endpoint used by CI/CD: `/wp-json/wp/v2/posts?per_page=100&page=1&_embed`
- Sends webhook on post change → triggers GitHub Actions
- Uploads stored in Docker volume mounted at `/var/www/sdd-demo/media` on host

### MySQL
- Docker container, internal network only
- Persistent Docker volume for data
- Password from AWS Secrets Manager (`db_password`)

### Astro (Frontend)
- Title: Eugenio Astro
- Mode: SSG — built to static files, no runtime container
- Public URL: `https://astro.4eng.online`
- Nginx serves `/var/www/sdd-demo/astro/dist` as static files
- Receives WP posts as markdown in `src/content/blog/` on every deploy

### Docusaurus (Docs/Blog)
- Title: Eugenio Docu
- Mode: SSG — blog-only config, blog at root `/`
- Dev server port: 3000
- Public URL: `https://docu.4eng.online`
- Nginx serves `/var/www/sdd-demo/docusaurus/build` as static files
- Receives same WP posts as `docusaurus/blog/YYYY-MM-DD-slug.md` on every deploy

---

## 6. Shared Media

WordPress uploads and Astro/Docusaurus image references share a single host path:

```
Host path:   /var/www/sdd-demo/media/
Docker mount: wordpress container → /var/www/html/wp-content/uploads
Nginx alias: /media/ → /var/www/sdd-demo/media/ (on all three domains)
```

Images uploaded to WordPress are instantly available at `/media/filename.jpg` on `wp.4eng.online`, `astro.4eng.online`, and `docu.4eng.online`. Content generators rewrite `wp-content/uploads/` URLs to `/media/` when generating markdown files.

---

## 7. Astro Frontend

### CategoryFilter (React Island)
- `client:load` hydration
- Toggle bar: **All** | **Sport** | **Travel** | **Uncategorized**
- Filters displayed posts client-side, no page reload

### LiveClock (React Island)
- `client:only="react"` — requires browser APIs, no SSR
- Updates every 1 second via `setInterval`
- Time format: `HH:mm:ss`
- Timezone: `Intl.DateTimeFormat().resolvedOptions().timeZone` → `Continent/City`
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

## 8. Docusaurus Frontend

- Blog-only mode (`docs: false` in preset config)
- Blog mounted at root path `/` via `routeBasePath: "/"`
- Sidebar shows all posts (`blogSidebarCount: "ALL"`)
- Posts have `title`, `date`, `tags` (one of: Sport, Travel, Uncategorized), `description` frontmatter
- File naming: `YYYY-MM-DD-slug.md` (Docusaurus convention for date extraction)

---

## 9. Routing (Nginx)

```
wp.4eng.online    → proxy_pass to localhost:8080          (WordPress container)
astro.4eng.online → root /var/www/sdd-demo/astro/dist     (static files, no proxy)
docu.4eng.online  → root /var/www/sdd-demo/docusaurus/build (static files, no proxy)

All three domains also serve:
  /media/ → alias /var/www/sdd-demo/media/  (shared WordPress uploads)
```

All domains: HTTPS enforced, HTTP redirects to HTTPS, Let's Encrypt certificates.

---

## 10. CI/CD (GitHub Actions)

**Trigger:** WordPress webhook on post create/update/delete → `repository_dispatch` event.

**Pipeline steps:**
1. `openspec validate` — abort if spec and implementation have drifted
2. Fetch all posts from `https://wp.4eng.online/wp-json/wp/v2/posts?per_page=100&page=1&_embed`
3. `node scripts/generate-content.js` — writes `astro/src/content/blog/*.md`
4. `node scripts/generate-docusaurus-content.js` — writes `docusaurus/blog/YYYY-MM-DD-*.md`
5. `npm run build` in `./astro` → outputs to `./astro/dist`
6. `npm run build` in `./docusaurus` → outputs to `./docusaurus/build`
7. rsync `./astro/dist/` to `astro.4eng.online:/var/www/sdd-demo/astro/dist/`
8. rsync `./docusaurus/build/` to `docu.4eng.online:/var/www/sdd-demo/docusaurus/build/`

Node version: `22` (required by Astro 7 / `>=22.12.0`).

---

## 11. OpenSpec Validator

**Entry point:** `python openspec/validate.py`

**Pass 1 — Schema validation**  
Validates `openspec.yaml` against `openspec.schema.json`. Catches missing required fields and invalid values.

**Pass 2 — Conformance checks**

| Module | Asserts |
|---|---|
| `terraform.py` | region, instance_type, SG inbound ports [22,80,443], Secrets Manager resources for all `secrets.keys`, IAM role name, `route53:ChangeResourceRecordSets` in policy, `aws_iam_instance_profile` present, EC2 `iam_instance_profile` set |
| `docker.py` | WordPress on port 8080, MySQL present, **no Astro service** (spec says `mode: ssg`) |
| `nginx.py` | All upstreams have a server block; static upstreams use `root` directive; proxy upstream uses `proxy_pass :port`; SSL blocks present; shared media `location /media/` and `alias` present |
| `cicd.py` | Webhook trigger present, fetch URL matches spec, `npm run build` step present, rsync deploy present, `openspec/validate.py` present, `docusaurus` step present (when docusaurus service in spec) |

**Output:**
```
[PASS] schema
[PASS] terraform
[PASS] docker
[PASS] nginx
[PASS] cicd

All checks passed.
```

**CI gate:** `deploy.yml` runs `openspec validate` as its first step. Deploy is blocked on any failure.

---

## 12. Key Constraints

- Astro and Docusaurus run in SSG mode — no containers in production
- Nginx serves both static sites' dist/build directories directly (not proxied)
- `openspec validate` must pass before any deploy
- All secrets stored in AWS Secrets Manager — no plaintext credentials in any file
- EC2 instance has IAM role with Route 53 permissions — no AWS credentials files needed on instance
- Shared `/media/` path means WordPress uploads are available at identical URLs on all three domains
- t3.small is sized for demo load only
- Node 22+ required (Astro 7 constraint)
- Categories: Sport, Travel, Uncategorized (Uncategorized is the fallback)
