# tests/openspec/test_validate.py
import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))

from openspec.validate import validate_schema

VALID_SPEC = {
    "meta": {"name": "test", "version": "1.0"},
    "infrastructure": {
        "provider": "aws",
        "region": "eu-central-1",
        "instance_type": "t3.small",
        "os": "ubuntu-24.04",
        "security_group": {
            "name": "sg-test",
            "inbound": [{"port": 22, "cidr": "0.0.0.0/0"}],
            "outbound": [{"port": "all", "cidr": "0.0.0.0/0"}],
        },
    },
    "secrets": {"store": "aws-secrets-manager", "keys": ["k1"]},
    "services": {
        "wordpress": {
            "title": "WP", "image": "wordpress:latest",
            "port": 8080, "domain": "wp.example.com", "categories": ["Sport"],
        },
        "mysql": {"image": "mysql:8.0", "secret_ref": "k1"},
        "astro": {
            "title": "Astro", "port": 4321, "domain": "astro.example.com",
            "mode": "ssg", "categories": ["Sport"],
        },
    },
    "routing": {
        "engine": "nginx", "ssl": "letsencrypt",
        "upstreams": [
            {"service": "wordpress", "domain": "wp.example.com", "proxy_port": 8080},
            {"service": "astro", "domain": "astro.example.com", "serve_static": "/path/dist"},
        ],
    },
    "cicd": {
        "provider": "github-actions",
        "trigger": "wordpress-webhook",
        "steps": [{"fetch_posts": {"url": "https://wp.example.com/wp-json/wp/v2/posts", "params": {"per_page": 100, "page": 1}}}],
    },
}


def test_valid_spec_passes():
    assert validate_schema(VALID_SPEC) == []


def test_missing_meta_fails():
    spec = {k: v for k, v in VALID_SPEC.items() if k != "meta"}
    errors = validate_schema(spec)
    assert len(errors) > 0


def test_invalid_provider_fails():
    spec = copy.deepcopy(VALID_SPEC)
    spec["infrastructure"]["provider"] = "gcp"
    errors = validate_schema(spec)
    assert len(errors) > 0


def test_invalid_astro_mode_fails():
    spec = copy.deepcopy(VALID_SPEC)
    spec["services"]["astro"]["mode"] = "invalid"
    errors = validate_schema(spec)
    assert len(errors) > 0
