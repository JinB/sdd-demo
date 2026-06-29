import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))

from openspec.checks.nginx import check

SPEC = {
    "services": {
        "wordpress": {"domain": "wp.bball.klarr.us", "port": 8080},
        "astro": {"domain": "astro.bball.klarr.us", "mode": "ssg"},
    },
    "routing": {
        "upstreams": [
            {"service": "wordpress", "domain": "wp.bball.klarr.us", "proxy_port": 8080},
            {"service": "astro", "domain": "astro.bball.klarr.us",
             "serve_static": "/var/www/sdd-demo/astro/dist"},
        ]
    },
}

VALID_NGINX = """\
server {
    listen 80;
    server_name wp.bball.klarr.us;
    return 301 https://$host$request_uri;
}
server {
    listen 443 ssl;
    server_name wp.bball.klarr.us;
    ssl_certificate /etc/letsencrypt/live/wp.bball.klarr.us/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/wp.bball.klarr.us/privkey.pem;
    location / {
        proxy_pass http://localhost:8080;
    }
}
server {
    listen 80;
    server_name astro.bball.klarr.us;
    return 301 https://$host$request_uri;
}
server {
    listen 443 ssl;
    server_name astro.bball.klarr.us;
    ssl_certificate /etc/letsencrypt/live/astro.bball.klarr.us/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/astro.bball.klarr.us/privkey.pem;
    root /var/www/sdd-demo/astro/dist;
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
    assert any("wp.bball.klarr.us" in f or "proxy_pass" in f for f in failures)


def test_astro_proxy_pass_fails(tmp_path):
    (tmp_path / "nginx").mkdir()
    conf = VALID_NGINX.replace(
        "root /var/www/sdd-demo/astro/dist;",
        "proxy_pass http://localhost:4321;",
    )
    (tmp_path / "nginx" / "default.conf").write_text(conf)
    failures = check(SPEC, base_dir=str(tmp_path))
    assert any("astro" in f.lower() or "root" in f for f in failures)


def test_missing_ssl_fails(tmp_path):
    (tmp_path / "nginx").mkdir()
    conf = "\n".join(
        l for l in VALID_NGINX.splitlines() if "ssl_certificate" not in l
    )
    (tmp_path / "nginx" / "default.conf").write_text(conf)
    failures = check(SPEC, base_dir=str(tmp_path))
    assert any("ssl" in f.lower() for f in failures)
