from pathlib import Path


def check(spec: dict, base_dir: str = ".") -> list[str]:
    conf_path = Path(base_dir, "nginx", "default.conf")
    if not conf_path.exists():
        return ["nginx/default.conf not found"]

    content = conf_path.read_text()
    failures: list[str] = []

    wp_domain = spec["services"]["wordpress"]["domain"]
    wp_port = spec["services"]["wordpress"]["port"]
    astro_domain = spec["services"]["astro"]["domain"]
    static_path = next(
        u["serve_static"]
        for u in spec["routing"]["upstreams"]
        if u["service"] == "astro"
    )

    if f"server_name {wp_domain}" not in content:
        failures.append(f"No server block for {wp_domain}")
    elif f"proxy_pass http://localhost:{wp_port}" not in content:
        failures.append(
            f"{wp_domain}: expected proxy_pass to port {wp_port}"
        )

    if f"server_name {astro_domain}" not in content:
        failures.append(f"No server block for {astro_domain}")
    else:
        if f"root {static_path}" not in content:
            failures.append(
                f"{astro_domain}: expected 'root {static_path}'"
            )

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
