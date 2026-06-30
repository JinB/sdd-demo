# sdd-demo

A spec-anchored WordPress/Astro/Docusaurus demo on a single AWS EC2 instance. `openspec.yaml` is the single source of truth — all infrastructure files conform to it and are validated before every deploy.

## Stack

- **WordPress** — content backend, Docker container on port 8080
- **MySQL** — database, Docker container (internal network only)
- **Astro** — static frontend (SSG), served by nginx from `astro/dist`
- **Docusaurus** — static blog (SSG), served by nginx from `docusaurus/build`
- **Nginx** — reverse proxy + static file server, Let's Encrypt SSL
- **Terraform** — provisions EC2 (`t3.small`, `eu-central-1`), security group, IAM role with Route 53 permissions, Secrets Manager secrets
- **GitHub Actions** — triggered by WordPress webhook; fetches posts, builds Astro + Docusaurus, deploys both via rsync

## OpenSpec Validator

Validates that all implementation files match `openspec.yaml` before every deploy.

```bash
pip install -r openspec/requirements.txt
python openspec/validate.py
```

Checks: schema, Terraform, Docker Compose, Nginx, CI/CD workflow.

## Astro Frontend

Categories: **Sport** | **Travel** | **Uncategorized**

Features:
- Category filter (React island, client-side)
- Live clock with browser timezone (`HH:mm:ss · Continent/City`)
- Dark/light mode toggle with localStorage persistence

```bash
cd astro
npm install
npm test       # 27 tests
npm run build  # outputs to astro/dist
```

## Docusaurus Frontend

Same WordPress posts published as a Docusaurus blog.

Features:
- Live clock with browser timezone (`HH:mm:ss · Continent/City`) in the navbar
- All-posts sidebar
- Tags: Sport / Travel / Uncategorized

```bash
cd docusaurus
npm install
npm run build  # outputs to docusaurus/build
npm start      # dev server at http://localhost:3000
```

## Domains

| Domain | Service |
|--------|---------|
| `wp.4eng.online` | WordPress (proxied from port 8080) |
| `astro.4eng.online` | Astro static site |
| `docu.4eng.online` | Docusaurus static blog |

All three domains share a `/media/` path for WordPress uploads.

## Secrets

Stored in AWS Secrets Manager under `sdd-demo/`:
- `db_password`
- `wp_admin_password`
- `gh_deploy_key`
