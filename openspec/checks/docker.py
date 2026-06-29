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
