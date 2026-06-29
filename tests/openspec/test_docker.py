import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[2]))

from openspec.checks.docker import check

SPEC = {
    "services": {
        "wordpress": {"port": 8080},
        "mysql": {},
        "astro": {"mode": "ssg"},
    }
}

VALID_COMPOSE = """\
services:
  wordpress:
    image: wordpress:latest
    ports:
      - "8080:80"
    networks:
      - wp-network
  mysql:
    image: mysql:8.0
    networks:
      - wp-network

networks:
  wp-network:
"""


def test_valid_compose_passes(tmp_path):
    (tmp_path / "docker-compose.yml").write_text(VALID_COMPOSE)
    assert check(SPEC, base_dir=str(tmp_path)) == []


def test_missing_wordpress_fails(tmp_path):
    compose = "services:\n  mysql:\n    image: mysql:8.0\n"
    (tmp_path / "docker-compose.yml").write_text(compose)
    failures = check(SPEC, base_dir=str(tmp_path))
    assert any("wordpress" in f for f in failures)


def test_wrong_wp_port_fails(tmp_path):
    compose = VALID_COMPOSE.replace('"8080:80"', '"9090:80"')
    (tmp_path / "docker-compose.yml").write_text(compose)
    failures = check(SPEC, base_dir=str(tmp_path))
    assert any("port" in f.lower() or "8080" in f for f in failures)


def test_astro_service_present_fails_when_ssg(tmp_path):
    compose = VALID_COMPOSE.replace(
        "  mysql:\n    image: mysql:8.0\n    networks:\n      - wp-network\n\n",
        "  mysql:\n    image: mysql:8.0\n    networks:\n      - wp-network\n  astro:\n    image: node:20\n\n"
    )
    (tmp_path / "docker-compose.yml").write_text(compose)
    failures = check(SPEC, base_dir=str(tmp_path))
    assert any("astro" in f for f in failures)


def test_missing_mysql_fails(tmp_path):
    compose = "services:\n  wordpress:\n    ports:\n      - '8080:80'\n"
    (tmp_path / "docker-compose.yml").write_text(compose)
    failures = check(SPEC, base_dir=str(tmp_path))
    assert any("mysql" in f for f in failures)
