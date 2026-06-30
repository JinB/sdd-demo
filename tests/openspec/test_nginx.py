import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))

from openspec.checks.nginx import check

SPEC = {
    "services": {
        "wordpress": {"domain": "wp.4eng.online", "port": 8080},
        "astro": {"domain": "astro.4eng.online", "mode": "ssg"},
        "docusaurus": {"domain": "docu.4eng.online", "mode": "ssg"},
    },
    "routing": {
        "upstreams": [
            {"service": "wordpress", "domain": "wp.4eng.online", "proxy_port": 8080},
            {"service": "astro", "domain": "astro.4eng.online",
             "serve_static": "/var/www/sdd-demo/astro/dist"},
            {"service": "docusaurus", "domain": "docu.4eng.online",
             "serve_static": "/var/www/sdd-demo/docusaurus/build"},
        ]
    },
}

VALID_NGINX = """\
server {
    listen 80;
    server_name wp.4eng.online;
    return 301 https://$host$request_uri;
}
server {
    listen 443 ssl;
    server_name wp.4eng.online;
    ssl_certificate /etc/letsencrypt/live/wp.4eng.online/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/wp.4eng.online/privkey.pem;
    location / {
        proxy_pass http://localhost:8080;
    }
}
server {
    listen 80;
    server_name astro.4eng.online;
    return 301 https://$host$request_uri;
}
server {
    listen 443 ssl;
    server_name astro.4eng.online;
    ssl_certificate /etc/letsencrypt/live/astro.4eng.online/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/astro.4eng.online/privkey.pem;
    root /var/www/sdd-demo/astro/dist;
    location / {
        try_files $uri $uri/ /index.html;
    }
}
server {
    listen 80;
    server_name docu.4eng.online;
    return 301 https://$host$request_uri;
}
server {
    listen 443 ssl;
    server_name docu.4eng.online;
    ssl_certificate /etc/letsencrypt/live/docu.4eng.online/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/docu.4eng.online/privkey.pem;
    root /var/www/sdd-demo/docusaurus/build;
    location / {
        try_files $uri $uri/ /index.html;
    }
}
"""


def test_valid_nginx_passes(tmp_path):
    (tmp_path / "nginx").mkdir()
    (tmp_path / "nginx" / "default.conf").write_text(VALID_NGINX)
    assert check(SPEC, base_dir=str(tmp_path)) == []


def test_wrong_wp_port_fails(tmp_path):
    (tmp_path / "nginx").mkdir()
    conf = VALID_NGINX.replace("localhost:8080", "localhost:9090")
    (tmp_path / "nginx" / "default.conf").write_text(conf)
    failures = check(SPEC, base_dir=str(tmp_path))
    assert any("wp.4eng.online" in f or "proxy_pass" in f for f in failures)


def test_astro_proxy_pass_fails(tmp_path):
    (tmp_path / "nginx").mkdir()
    conf = VALID_NGINX.replace(
        "root /var/www/sdd-demo/astro/dist;",
        "proxy_pass http://localhost:4321;",
    )
    (tmp_path / "nginx" / "default.conf").write_text(conf)
    failures = check(SPEC, base_dir=str(tmp_path))
    assert any("astro" in f.lower() or "root" in f for f in failures)


def test_missing_docu_block_fails(tmp_path):
    (tmp_path / "nginx").mkdir()
    conf = "\n".join(
        l for l in VALID_NGINX.splitlines() if "docu.4eng.online" not in l
    )
    (tmp_path / "nginx" / "default.conf").write_text(conf)
    failures = check(SPEC, base_dir=str(tmp_path))
    assert any("docu.4eng.online" in f for f in failures)


def test_missing_ssl_fails(tmp_path):
    (tmp_path / "nginx").mkdir()
    conf = "\n".join(
        l for l in VALID_NGINX.splitlines() if "ssl_certificate" not in l
    )
    (tmp_path / "nginx" / "default.conf").write_text(conf)
    failures = check(SPEC, base_dir=str(tmp_path))
    assert any("ssl" in f.lower() for f in failures)
