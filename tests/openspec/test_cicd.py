import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))

from openspec.checks.cicd import check

SPEC = {
    "services": {
        "docusaurus": {"domain": "docu.4eng.online", "mode": "ssg"},
    },
    "cicd": {
        "triggers": ["wordpress-webhook", "manual"],
        "pipeline": [
            {
                "fetch_posts": {
                    "url": "https://wp.4eng.online/wp-json/wp/v2/posts",
                    "params": {"per_page": 100, "page": 1},
                }
            }
        ],
    },
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
          curl -s "https://wp.4eng.online/wp-json/wp/v2/posts?per_page=100&page=1" -o posts.json
      - name: Build Astro
        run: npm run build
        working-directory: ./astro
      - name: Build Docusaurus
        run: npm run build
        working-directory: ./docusaurus
      - name: Deploy
        run: |
          rsync -avz -e "ssh -i ~/.ssh/deploy_key" ./astro/dist/ ubuntu@astro.4eng.online:/var/www/sdd-demo/astro/dist/
          rsync -avz -e "ssh -i ~/.ssh/deploy_key" ./docusaurus/build/ ubuntu@docu.4eng.online:/var/www/sdd-demo/docusaurus/build/
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
        "https://wp.4eng.online/wp-json/wp/v2/posts", "https://example.com"
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


def test_missing_docusaurus_step_fails(tmp_path):
    gh_dir = tmp_path / ".github" / "workflows"
    gh_dir.mkdir(parents=True)
    workflow = "\n".join(
        l for l in VALID_WORKFLOW.splitlines() if "docusaurus" not in l
    )
    (gh_dir / "deploy.yml").write_text(workflow)
    failures = check(SPEC, base_dir=str(tmp_path))
    assert any("docusaurus" in f.lower() for f in failures)
