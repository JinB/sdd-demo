# sdd-demo

A spec-anchored WordPress/Astro demo on a single AWS EC2 instance. `openspec.yaml` is the single source of truth — all infrastructure files conform to it and are validated before every deploy.

## Stack

- **WordPress** — content backend, Docker container on port 8080
- **MySQL** — database, Docker container (internal network only)
- **Astro** — static frontend (SSG), served by nginx from `astro/dist`
- **Nginx** — reverse proxy + static file server, Let's Encrypt SSL
- **Terraform** — provisions EC2 (`t3.small`, `eu-central-1`), security group, Secrets Manager secrets
- **GitHub Actions** — triggered by WordPress webhook; fetches posts, builds Astro, deploys via rsync

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
npm test       # 16 tests
npm run build  # outputs to astro/dist
```

## Domains

| Domain | Service |
|--------|---------|
| `wp.bball.klarr.us` | WordPress (proxied from port 8080) |
| `astro.bball.klarr.us` | Astro static site |

## Secrets

Stored in AWS Secrets Manager under `sdd-demo/`:
- `db_password`
- `wp_admin_password`
- `gh_deploy_key`
