#!/usr/bin/env python3
import json
import sys
from pathlib import Path

import jsonschema
import yaml

_SCHEMA_PATH = Path(__file__).parent / "schema" / "openspec.schema.json"


def load_spec(path: str = "openspec.yaml") -> dict:
    return yaml.safe_load(Path(path).read_text())


def validate_schema(spec: dict) -> list[str]:
    schema = json.loads(_SCHEMA_PATH.read_text())
    errors = []
    try:
        jsonschema.validate(spec, schema)
    except jsonschema.ValidationError as e:
        errors.append(e.message)
    return errors


def _run_checks(spec: dict) -> dict[str, list[str]]:
    from openspec.checks import terraform, docker, nginx, cicd
    return {
        "terraform": terraform.check(spec),
        "docker": docker.check(spec),
        "nginx": nginx.check(spec),
        "cicd": cicd.check(spec),
    }


def main() -> int:
    try:
        spec = load_spec()
    except FileNotFoundError:
        print("[FAIL] openspec.yaml not found")
        return 1

    schema_errors = validate_schema(spec)
    if schema_errors:
        print(f"[FAIL] schema\n       → {schema_errors[0]}")
        return 1
    print("[PASS] schema")

    failed = 0
    for name, failures in _run_checks(spec).items():
        if failures:
            print(f"[FAIL] {name}")
            for f in failures:
                print(f"       → {f}")
            failed += 1
        else:
            print(f"[PASS] {name}")

    if failed:
        print(f"\n{failed} check{'s' if failed > 1 else ''} failed.")
        return 1
    print("\nAll checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
