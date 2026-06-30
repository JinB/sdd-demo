from pathlib import Path

import yaml


def check(spec: dict, base_dir: str = ".") -> list[str]:
    workflow_path = Path(base_dir, ".github", "workflows", "deploy.yml")
    if not workflow_path.exists():
        return [".github/workflows/deploy.yml not found"]

    data = yaml.safe_load(workflow_path.read_text())
    failures: list[str] = []

    # PyYAML 1.1 parses bare `on:` key as boolean True
    triggers = data.get(True) or data.get("on") or {}
    if "repository_dispatch" not in triggers:
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

    if "docusaurus" in spec.get("services", {}):
        if "docusaurus" not in combined:
            failures.append("docusaurus build/deploy step not found in workflow")

    if "nextjs" in spec.get("services", {}):
        if "nextjs" not in combined:
            failures.append("nextjs build/deploy step not found in workflow")

    return failures
