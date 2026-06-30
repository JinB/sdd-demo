from pathlib import Path


def check(spec: dict, base_dir: str = ".") -> list[str]:
    conf_path = Path(base_dir, "nginx", "default.conf")
    if not conf_path.exists():
        return ["nginx/default.conf not found"]

    content = conf_path.read_text()
    failures: list[str] = []

    for upstream in spec["routing"]["upstreams"]:
        service = upstream["service"]
        domain = upstream.get("domain") or spec["services"][service]["domain"]

        if f"server_name {domain}" not in content:
            failures.append(f"No server block for {domain}")
        elif "serve_static" in upstream:
            static_path = upstream["serve_static"]
            if f"root {static_path}" not in content:
                failures.append(f"{domain}: expected 'root {static_path}'")
        elif "proxy_port" in upstream:
            port = upstream["proxy_port"]
            if f"proxy_pass http://localhost:{port}" not in content:
                failures.append(f"{domain}: expected proxy_pass to port {port}")

    if "ssl_certificate" not in content:
        failures.append("SSL certificates not configured in nginx/default.conf")

    shared_media = spec.get("routing", {}).get("shared_media")
    if shared_media:
        media_host_path = shared_media["host_path"]
        media_url_path = shared_media["url_path"].strip("/")
        if f"location /{media_url_path}/" not in content:
            failures.append(
                f"shared_media: location /{media_url_path}/ not found in nginx config"
            )
        elif f"alias {media_host_path}/" not in content:
            failures.append(
                f"shared_media: expected alias {media_host_path}/ in /{media_url_path}/ block"
            )

    return failures
