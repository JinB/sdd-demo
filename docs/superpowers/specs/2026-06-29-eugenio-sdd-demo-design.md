# Eugenio SDD Demo — Design Spec

**Date:** 2026-06-29
**Last updated:** 2026-07-01 (Next.js; site nav; per-site deploy; WP trigger plugin; SendGrid HTML notifications; dynamic DNS on boot with boot email; About page; SiteNav rework; DMARC email authentication; Next.js nextjs.org palette + Geist font; active SiteNav link clickable; Docusaurus mobile navbar left-align)
**Approach:** OpenSpec Spec-Anchored
**Status:** Approved — implemented and live

---

## 1. Overview

A WordPress/Astro/Docusaurus/Next.js demo managed by OpenSpec using a Spec-Anchored development flow. A single `openspec.yaml` is the source of truth; all implementation files (Terraform, Docker Compose, Nginx, GitHub Actions) must conform to it. A validator CLI enforces conformance locally and as a CI gate.

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
        timezone: Intl
      site_nav: true
    categories: [Sport, Travel, Uncategorized]

  docusaurus:
    title: Eugenio Docusaurus
    port: 3000            # dev only; prod = static files served by nginx
    domain: docu.4eng.online
    mode: ssg
    build_output: build
    features:
      live_clock:
        format: HH:mm:ss
        timezone: Intl
      site_nav: true

  nextjs:
    title: Eugenio Next.js
    port: 3001            # dev only; prod = static files served by nginx
    domain: next.4eng.online
    mode: ssg
    build_output: out
    features:
      dark_light_switcher: true
      live_clock:
        format: HH:mm:ss
        timezone: Intl
      site_nav: true

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
    - service: nextjs
      domain: next.4eng.online
      serve_static: /var/www/sdd-demo/nextjs/out

cicd:
  provider: github-actions
  triggers:
    - wordpress-webhook
    - manual
  node_version: "22"
  pipeline:
    - validate_openspec
    - fetch_posts:
        url: "https://wp.4eng.online/wp-json/wp/v2/posts"
        params: { per_page: 100, page: 1 }
    - astro:
        generate: scripts/generate-content.js
        build_dir: ./astro
        deploy: ubuntu@astro.4eng.online:/var/www/sdd-demo/astro/dist/
    - nextjs:
        generate: scripts/generate-nextjs-content.js
        build_dir: ./nextjs
        deploy: ubuntu@next.4eng.online:/var/www/sdd-demo/nextjs/out/
    - docusaurus:
        generate: scripts/generate-docusaurus-content.js
        build_dir: ./docusaurus
        deploy: ubuntu@docu.4eng.online:/var/www/sdd-demo/docusaurus/build/
  deploy_method: rsync-ssh
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
│   ├── generate-content.js             ← WP posts → astro/src/content/blog/
│   ├── generate-docusaurus-content.js  ← WP posts → docusaurus/blog/
│   └── generate-nextjs-content.js      ← WP posts → nextjs/src/data/posts.json
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
│   │   │   ├── SiteNav.astro      ← inter-site navigation bar
│   │   │   ├── Header.astro       ← sticky header with LiveClock + ThemeToggle
│   │   │   └── Footer.astro       ← about text
│   │   ├── pages/
│   │   │   ├── index.astro
│   │   │   └── blog/[id].astro
│   │   └── styles/global.css
│   ├── astro.config.mjs
│   └── package.json
│
├── docusaurus/
│   ├── docusaurus.config.js       ← blog-only mode, root path /
│   ├── package.json
│   ├── blog/                      ← replaced by CI/CD on every deploy
│   └── src/
│       ├── css/custom.css
│       ├── components/
│       │   ├── LiveClock.js
│       │   └── SiteNav.js         ← inter-site navigation bar
│       └── theme/
│           ├── NavbarItem/ComponentTypes.js
│           └── Root.js            ← injects SiteNav above all content
│
└── nextjs/
    ├── next.config.ts             ← output: "export", trailingSlash: true
    ├── package.json
    └── src/
        ├── app/
        │   ├── layout.tsx         ← root layout with Header + SiteNav + Footer
        │   ├── globals.css
        │   ├── page.tsx           ← blog listing with category filter
        │   └── blog/[slug]/
        │       └── page.tsx       ← post detail page
        ├── components/
        │   ├── Header.tsx         ← sticky header with LiveClock + ThemeToggle
        │   ├── SiteNav.tsx        ← inter-site navigation bar
        │   ├── Footer.tsx         ← about text
        │   ├── LiveClock.tsx
        │   └── ThemeToggle.tsx
        ├── lib/posts.ts           ← reads posts.json, exports getPosts / getPost
        └── data/posts.json        ← generated by CI/CD, git-ignored
```

---

## 4. Infrastructure

**EC2**
- Region: `eu-central-1`
- OS: Ubuntu 24.04
- Instance type: `t3.small` (2 vCPU, 2 GB RAM)
- Security group `sg-spec-demo`: inbound 22/80/443 from all; outbound unrestricted
- No Elastic IP — public IP is dynamic; Route 53 is updated automatically on every boot (see §16)

**IAM**
- Role: `sdd-demo-ec2-role` — attached to the EC2 instance via instance profile
- Inline policy `route53_update`: allows `route53:ChangeResourceRecordSets`, `GetChange`, `ListHostedZones`, `ListResourceRecordSets`
- Purpose: enables Certbot DNS-01 challenge and programmatic Route 53 updates from the instance

**Stack on EC2**
- Nginx on host (80/443) — reverse proxy + static file server
- Docker Compose manages: WordPress (port 8080), MySQL (internal only)
- WordPress uploads mounted to host at `/var/www/sdd-demo/media` (bind mount)
- Astro, Docusaurus, and Next.js are build-only — no containers in production; built static files served directly by Nginx
- Let's Encrypt SSL via Certbot with auto-renewal cron

**Secrets**

| Secret | Store | Used by |
|--------|-------|---------|
| `db_password` | AWS Secrets Manager | Docker Compose / MySQL |
| `wp_admin_password` | AWS Secrets Manager | WordPress setup |
| `GH_DEPLOY_KEY` | GitHub Actions secret | rsync SSH to server |
| `GH_DEPLOY_TOKEN` | Server `.env` file | WP trigger plugin → GitHub API |
| `SENDGRID_API_KEY` | GitHub Actions secret + Server `.env` | CI/CD deploy emails + EC2 boot email |

Docker Compose reads DB credentials and `GH_DEPLOY_TOKEN` via environment at startup. `SENDGRID_API_KEY` lives in both GitHub Actions secrets (deploy pipeline) and the server's `.env` (boot notification via `update-dns.sh`).

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
- Title: Eugenio Docusaurus
- Mode: SSG — blog-only config, blog at root `/`
- Dev server port: 3000
- Public URL: `https://docu.4eng.online`
- Nginx serves `/var/www/sdd-demo/docusaurus/build` as static files
- Receives same WP posts as `docusaurus/blog/YYYY-MM-DD-slug.md` on every deploy

### Next.js (Frontend)
- Title: Eugenio Next.js
- Mode: SSG — `output: "export"`, built to `out/`, no runtime container
- Dev server port: 3001
- Public URL: `https://next.4eng.online`
- Nginx serves `/var/www/sdd-demo/nextjs/out` as static files
- Receives WP posts as JSON in `src/data/posts.json` on every deploy

---

## 6. Shared Media

WordPress uploads and all three SSG sites share a single host path:

```
Host path:    /var/www/sdd-demo/media/
Docker mount: wordpress container → /var/www/html/wp-content/uploads
Nginx alias:  /media/ → /var/www/sdd-demo/media/ (on all four domains)
```

Images uploaded to WordPress are instantly available at `/media/filename.jpg` on all four domains. Content generators rewrite `wp-content/uploads/` URLs (any domain) to the site's own `/media/` path.

---

## 7. Shared Site Nav Bar

A 2rem-high horizontal bar rendered below the main header on every page of all three SSG sites. Bar contents (same on all sites):

```
[About]  [Astro]  [Docu]  [Next.js]  [WP]  |  [Admin ↗]  [GitHub ↗]
```

| Link | URL | Behaviour |
|------|-----|-----------|
| About | `/about` | same tab — intra-site About page |
| Astro | `https://astro.4eng.online` | same tab |
| Docu | `https://docu.4eng.online` | same tab |
| Next.js | `https://next.4eng.online` | same tab |
| WP | `https://wp.4eng.online` | same tab — public WP site |
| Admin ↗ | `https://wp.4eng.online/wp-admin/edit.php` | new tab |
| GitHub ↗ | `https://github.com/JinB/sdd-demo` | new tab |

- Current site rendered as `<a href="/" class="site-nav-link active">` — clickable, navigates to home (allows browsing back from About or any sub-page)
- Separator is a 1px vertical line

Implementation per framework:
- **Astro**: `SiteNav.astro` injected after `<Header />` in each page template
- **Docusaurus**: `src/theme/Root.js` swizzle injects `SiteNav.js` before `{children}`
- **Next.js**: `SiteNav.tsx` injected after `<Header />` in root `layout.tsx`

---

## 8. Astro Frontend

### CategoryFilter (React Island)
- `client:load` hydration
- Toggle bar: **All** + any WP category (dynamically derived from posts, no hardcoded list)
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
- Toggles dark/light mode, persists via `localStorage`

### Header
- Sticky, `backdrop-filter: blur(12px)`
- Contains: `LiveClock` and `ThemeToggle`

### Design System
- CSS custom properties: zinc palette for neutrals, indigo for accent
- Dark mode via `.dark` class on `:root`
- Anti-FOUC: inline `<script>` in `<head>` reads `localStorage` and applies `.dark` before React hydration

---

## 9. Docusaurus Frontend

- Blog-only mode (`docs: false` in preset config)
- Blog mounted at root path `/` via `routeBasePath: "/"`
- Sidebar shows all posts (`blogSidebarCount: "ALL"`)
- Posts have `title`, `date`, `tags`, `description` frontmatter; images injected as markdown `![](url)` in body
- File naming: `YYYY-MM-DD-slug.md` (Docusaurus convention for date extraction)
- Navbar title **"Eugenio Docusaurus"** is centered via CSS (`position: absolute; left: 50%; transform: translateX(-50%)`)
- On narrow screens (≤480px) the absolute centering is reset and the title is left-aligned in normal flow (avoids overlap with the LiveClock)

### LiveClock (Navbar Item)
- Registered as a custom navbar item type via `src/theme/NavbarItem/ComponentTypes.js` (Docusaurus swizzle pattern)
- Client-only: returns null until hydrated (`useEffect` sets time on mount)
- Renders `HH:mm:ss · Continent/City` in the navbar, right-aligned

---

## 10. Next.js Frontend

- Next.js 15 SSG: `output: "export"`, `trailingSlash: true`, `images: { unoptimized: true }`
- Posts loaded from `src/data/posts.json` (generated by CI/CD, git-ignored)
- Dynamic post pages: `generateStaticParams()` + `async function Page({ params: Promise<{slug}> })` (Next.js 15 async params)

### Dark Mode (Anti-FOUC)
- Inline `<script>` in `<head>` reads `localStorage` and applies `.dark` class before React hydration
- `suppressHydrationWarning` on `<html>` prevents hydration mismatch
- `ThemeToggle.tsx` is a `"use client"` component

### LiveClock
- `"use client"` component, `setInterval` every 1 second
- Same `Intl.DateTimeFormat` timezone source as Astro

### Design System
- Palette matches **nextjs.org**: pure white/black backgrounds, `#0070F3` blue accent
  - Light: `--bg: #ffffff`, `--text: #000000`, `--accent: #0070f3`
  - Dark: `--bg: #000000`, `--bg-secondary: #111111`, `--text: #ffffff`, `--accent: #0070f3`
- **Font**: Geist (Next.js's own typeface) loaded via `next/font/google`, exposed as `--font-geist` CSS variable
- **Border radius**: `0.25rem` (sharper than Astro's `0.5rem`)
- **Filter buttons and badges**: rectangular (`var(--radius)`), not pill-shaped
- **Card hover in dark mode**: blue `box-shadow: 0 0 0 1px var(--accent)` outline instead of drop shadow

---

## 11. Routing (Nginx)

```
wp.4eng.online    → proxy_pass to localhost:8080            (WordPress container)
astro.4eng.online → root /var/www/sdd-demo/astro/dist       (static files)
docu.4eng.online  → root /var/www/sdd-demo/docusaurus/build (static files)
next.4eng.online  → root /var/www/sdd-demo/nextjs/out       (static files)

All four domains also serve:
  /media/ → alias /var/www/sdd-demo/media/  (shared WordPress uploads)
```

All domains: HTTPS enforced, HTTP redirects to HTTPS, single SAN Let's Encrypt certificate.

---

## 12. WordPress Auto-Deploy Trigger

A small plugin at `wp-plugins/sdd-deploy-trigger/sdd-deploy-trigger.php` hooks into `save_post` and calls the GitHub API whenever a post is published or updated:

```
POST https://api.github.com/repos/JinB/sdd-demo/dispatches
{ "event_type": "wordpress-post-change" }
Authorization: Bearer <GH_DEPLOY_TOKEN>
```

The plugin file is bind-mounted into the WordPress container via `docker-compose.yml`:
```yaml
volumes:
  - /var/www/sdd-demo/wp-plugins/sdd-deploy-trigger:/var/www/html/wp-content/plugins/sdd-deploy-trigger
```

`GH_DEPLOY_TOKEN` is a GitHub fine-grained PAT with **Contents: Read and write** permission (required for `repository_dispatch`), passed to the container via the `GH_DEPLOY_TOKEN` env var in the server's `.env` file. The plugin reads it with `getenv('GH_DEPLOY_TOKEN')`.

After the container is started with the mount in place, activate the plugin in WP Admin → Plugins.

---

## 13. CI/CD (GitHub Actions)

**Triggers:**
- WordPress webhook on post create/update/delete → `repository_dispatch: wordpress-post-change`
- Manual via GitHub Actions UI or `gh workflow run deploy.yml` → `workflow_dispatch`

**Pipeline (sequential, deploy after each build):**

1. `openspec validate` — abort if spec and implementation have drifted
2. Fetch all posts from `https://wp.4eng.online/wp-json/wp/v2/posts?per_page=100&page=1&_embed`
3. Setup SSH key from `GH_DEPLOY_KEY` secret
4. Record pipeline start time (`TZ=Europe/Prague date`) → `$GITHUB_ENV`
5. **Astro** (`id: astro`, `continue-on-error: true`): npm install → generate → build → `ssh mkdir -p` → rsync `astro/dist/`
6. **Next.js** (`id: nextjs`, `continue-on-error: true`): npm install → generate → build → `ssh mkdir -p` → rsync `nextjs/out/`
7. **Docusaurus** (`id: docusaurus`, `continue-on-error: true`): npm install → generate → build → `ssh mkdir -p` → rsync `docusaurus/build/`
8. **Notify** (`if: always()`): Python script sends HTML email via SendGrid to `eugenio.besson@gmail.com`

Each site is a **single workflow step** (install + generate + build + deploy combined). `continue-on-error: true` means a failing site doesn't abort the others — all three always attempt to deploy. Step `id`s expose `steps.<id>.outcome` (`success` / `failure` / `skipped`) to the Notify step.

**Notification email (HTML, `text/html`):**
```
✅ All sites deployed  —  Run #42

Started:   17:30 CEST, 30 Jun 2026
Finished:  17:47 CEST, 30 Jun 2026

Sites:
  ✅  Astro       https://astro.4eng.online    ← clickable link
  ✅  Next.js     https://next.4eng.online     ← clickable link
  ❌  Docusaurus  https://docu.4eng.online     ← clickable link

Run log: GitHub Actions #42                   ← clickable link
```

Icons: `✅` success · `❌` failure · `⏭️` skipped (earlier step in the job failed before this site ran).
Sent via Python `urllib.request` + SendGrid API v3. `zoneinfo.ZoneInfo("Europe/Prague")` provides CEST/CET timestamps.

Node version: `22` (required by Astro 7 / `>=22.12.0`).

---

## 14. OpenSpec Validator

**Entry point:** `python openspec/validate.py`

**Pass 1 — Schema validation**
Validates `openspec.yaml` against `openspec.schema.json`. Catches missing required fields and invalid values.

**Pass 2 — Conformance checks**

| Module | Asserts |
|---|---|
| `terraform.py` | region, instance_type, SG inbound ports [22,80,443], Secrets Manager resources for all `secrets.keys`, IAM role name, `route53:ChangeResourceRecordSets` and `route53:ListHostedZonesByName` in policy, `aws_iam_instance_profile` present, EC2 `iam_instance_profile` set |
| `docker.py` | WordPress on port 8080, MySQL present, **no Astro/Next.js/Docusaurus service** (spec says `mode: ssg`) |
| `nginx.py` | All upstreams have a server block; static upstreams use `root` directive; proxy upstream uses `proxy_pass :port`; SSL blocks present; shared media `location /media/` and `alias` present |
| `cicd.py` | Webhook trigger present, fetch URL matches spec, `npm run build` step present, rsync deploy present, `openspec/validate.py` present, nextjs and docusaurus steps present |

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

## 16. Dynamic DNS + Boot Email (Route 53 on start)

No Elastic IP is used — the EC2 public IP changes on every start. A systemd one-shot service runs `update-dns.sh` after the network is online, updates all four A records via the AWS CLI, then sends a SendGrid notification email with the new IP and clickable site links.

**Files (committed to repo under `server/`):**
- `server/update-dns.sh` — fetches public IP via IMDSv2, upserts all A records in one Route 53 batch call, sends HTML email via SendGrid
- `server/update-dns.service` — systemd unit: `After=network-online.target`, `Type=oneshot`

**Subdomains updated:** `wp`, `astro`, `docu`, `next` (all pointing to the same EC2 IP)  
**TTL:** 60 seconds — propagates within a minute of instance start  
**Auth:** EC2 IAM instance role `sdd-demo-ec2-role` with `route53_update` policy — no AWS credentials needed on the instance  
**Email:** sources `SENDGRID_API_KEY` from `/var/www/sdd-demo/.env`; skips gracefully if key is absent  
**Sender:** `4eng <noreply@4eng.online>` — authenticated via SendGrid domain authentication (DKIM + SPF for `4eng.online`)

**Notification email:**
```
From:    4eng <noreply@4eng.online>
Subject: EC2 started: 52.59.224.125

DNS updated
18:50 CEST, 30 Jun 2026

New IP: 52.59.224.125

Sites:
  https://wp.4eng.online
  https://astro.4eng.online
  https://docu.4eng.online
  https://next.4eng.online
```

**One-time server setup:**
```bash
cd /var/www/sdd-demo && git pull
sudo cp server/update-dns.sh /usr/local/bin/update-dns.sh
sudo chmod +x /usr/local/bin/update-dns.sh
sudo cp server/update-dns.service /etc/systemd/system/update-dns.service
sudo systemctl daemon-reload
sudo systemctl enable update-dns
echo "SENDGRID_API_KEY=your_key_here" >> /var/www/sdd-demo/.env
sudo systemctl start update-dns   # test immediately
journalctl -u update-dns -n 30    # verify
```

---

## 17. Email Authentication (DMARC / SPF / DKIM)

All outgoing SendGrid emails use `From: 4eng <noreply@4eng.online>`. Sending from a Gmail address through SendGrid caused DMARC failures and spam classification.

**DNS records on `4eng.online` (Route 53):**

| Name | Type | Value |
|------|------|-------|
| `4eng.online` | TXT | `"v=spf1 include:sendgrid.net ~all"` |
| `_dmarc.4eng.online` | TXT | `"v=DMARC1; p=none; rua=mailto:eugenio.besson@gmail.com"` |
| `em3768.4eng.online` | CNAME | `u110072772.wl023.sendgrid.net` |
| `s1._domainkey.4eng.online` | CNAME | `s1.domainkey.u110072772.wl023.sendgrid.net` |
| `s2._domainkey.4eng.online` | CNAME | `s2.domainkey.u110072772.wl023.sendgrid.net` |

**SendGrid:** domain `4eng.online` authenticated and verified under Settings → Sender Authentication.

**Result:** DKIM passes for `4eng.online`, SPF passes, DMARC alignment passes → inbox delivery.

---

## 15. Key Constraints

- Astro, Docusaurus, and Next.js run in SSG mode — no containers in production
- Nginx serves all three static sites' output directories directly (not proxied)
- `openspec validate` must pass before any deploy
- All secrets stored in AWS Secrets Manager — no plaintext credentials in any file
- EC2 instance has IAM role with Route 53 permissions — no AWS credentials files needed on instance
- Shared `/media/` path means WordPress uploads are available at identical URLs on all four domains
- Content generators rewrite any `wp-content/uploads/<any-domain>/` URL to the site's own `/media/` path
- t3.small is sized for demo load only
- Node 22+ required (Astro 7 constraint)
- Categories: Sport, Travel, Uncategorized (Uncategorized is the fallback)
- Build and deploy order: Astro → Next.js → Docusaurus; each site is deployed immediately after its build
