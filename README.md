# Spec Driven Development (OpenSpec) Demo

# Spec-Anchored WordPress/Astro/Docusaurus/Next.js

A single AWS EC2 instance running four web properties from one codebase.
`openspec.yaml` is the single source of truth — every infrastructure file
(Terraform, Docker Compose, Nginx, GitHub Actions) is validated against it
before each deploy.

**Live sites:**

| Site              | URL                       | Framework          |
| ----------------- | ------------------------- | ------------------ |
| Blog (Astro)      | https://astro.4eng.online | Astro 7 SSG        |
| Blog (Docusaurus) | https://docu.4eng.online  | Docusaurus 3 SSG   |
| Blog (Next.js)    | https://next.4eng.online  | Next.js 15 SSG     |
| CMS               | https://wp.4eng.online    | WordPress (Docker) |

---

## How it works

1. A post is published or updated in WordPress
2. A lightweight WP plugin fires a `repository_dispatch` webhook to GitHub
3. GitHub Actions validates the spec, fetches posts from the WP REST API, then for each SSG site: generates content → builds → deploys via rsync
4. A SendGrid email confirms success or reports failure

All three SSG sites show the same WordPress content rendered with different frameworks, making it easy to compare them side by side.

---

## Stack

| Layer               | Technology                                            |
| ------------------- | ----------------------------------------------------- |
| Content backend     | WordPress + MySQL (Docker Compose)                    |
| Static sites        | Astro 7 · Docusaurus 3.7 · Next.js 15 (all SSG)       |
| Reverse proxy / SSL | Nginx + Let's Encrypt (SAN cert, one for all domains) |
| Infrastructure      | Terraform → AWS EC2 `t3.small` `eu-central-1`         |
| Secrets             | AWS Secrets Manager · GitHub Actions secrets          |
| CI/CD               | GitHub Actions — webhook-triggered or manual          |
| Email alerts        | SendGrid API                                          |

---

## Features (all three SSG sites)

- **Live clock** — `HH:mm:ss · Continent/City` in the header, browser timezone via `Intl`
- **Dark / light mode** — persisted in `localStorage`, flash-free on load
- **Category filter** — client-side, no page reload
- **Inter-site nav bar** — links between Astro, Docusaurus, Next.js and WP Admin; current site highlighted
- **Featured images** — extracted from WP posts, served from a shared `/media/` path on all domains
- **About footer** — each site describes its own framework pros and cons

---

## Spec-Anchored Development

`openspec.yaml` defines the entire system. The validator checks conformance across all implementation files:

```bash
pip install -r openspec/requirements.txt
python openspec/validate.py
```

```
[PASS] schema
[PASS] terraform
[PASS] docker
[PASS] nginx
[PASS] cicd

All checks passed.
```

The `Validate OpenSpec` step runs first in every CI/CD pipeline run — a drift between spec and implementation blocks the deploy.

---

## Local development

```bash
# Astro
cd astro && npm install && npm run dev      # http://localhost:4321

# Next.js
cd nextjs && npm install && npm run dev     # http://localhost:3001

# Docusaurus
cd docusaurus && npm install && npm start   # http://localhost:3000
```

Generate content from WordPress (requires `posts.json`):

```bash
curl -s "https://wp.4eng.online/wp-json/wp/v2/posts?per_page=100&page=1&_embed" -o posts.json
node scripts/generate-content.js
node scripts/generate-nextjs-content.js
node scripts/generate-docusaurus-content.js
```

---

## Secrets

| Secret              | Where stored          | Used by                    |
| ------------------- | --------------------- | -------------------------- |
| `db_password`       | AWS Secrets Manager   | Docker Compose / MySQL     |
| `wp_admin_password` | AWS Secrets Manager   | WordPress setup            |
| `GH_DEPLOY_KEY`     | GitHub Actions secret | rsync SSH to server        |
| `GH_DEPLOY_TOKEN`   | Server `.env` file    | WP plugin → GitHub API     |
| `SENDGRID_API_KEY`  | GitHub Actions secret | Deploy email notifications |
