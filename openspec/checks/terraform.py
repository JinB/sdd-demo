from pathlib import Path

import hcl2


def _load_all_tf(base_dir: str) -> dict:
    merged: dict = {}
    for tf_file in Path(base_dir, "terraform").glob("*.tf"):
        try:
            with open(tf_file) as f:
                data = hcl2.load(f)
        except Exception:
            # Skip files that cannot be parsed (e.g. truncated/invalid HCL)
            continue
        for key, value in data.items():
            merged.setdefault(key, [])
            merged[key].extend(value)
    return merged


def _var_default(tf: dict, name: str) -> str | None:
    for block in tf.get("variable", []):
        if name in block:
            return block[name].get("default")
    return None


def _resolve(value: str, tf: dict) -> str:
    if isinstance(value, str) and value.startswith("${var.") and value.endswith("}"):
        return _var_default(tf, value[6:-1]) or value
    return value


def check(spec: dict, base_dir: str = ".") -> list[str]:
    tf_dir = Path(base_dir, "terraform")
    if not tf_dir.exists():
        return ["terraform/ directory not found"]

    tf = _load_all_tf(base_dir)
    failures: list[str] = []

    # Region check (via variable default)
    expected_region = spec["infrastructure"]["region"]
    actual_region = _var_default(tf, "region")
    if actual_region != expected_region:
        failures.append(
            f"region: expected {expected_region}, found {actual_region}"
        )

    # Instance type check (via variable default)
    expected_type = spec["infrastructure"]["instance_type"]
    actual_type = _var_default(tf, "instance_type")
    if actual_type != expected_type:
        failures.append(
            f"instance_type: expected {expected_type}, found {actual_type}"
        )

    # Security group inbound ports
    expected_ports = {
        int(r["port"]) for r in spec["infrastructure"]["security_group"]["inbound"]
        if str(r["port"]).isdigit()
    }
    actual_ports: set[int] = set()
    for block in tf.get("resource", []):
        for sg_config in block.get("aws_security_group", {}).values():
            for rule in sg_config.get("ingress", []):
                fp = rule.get("from_port")
                if fp is not None:
                    actual_ports.add(int(fp))

    missing_ports = expected_ports - actual_ports
    for port in sorted(missing_ports):
        failures.append(f"SG inbound port {port} not found in security group")

    # Secrets Manager resources
    actual_secrets: set[str] = set()
    for block in tf.get("resource", []):
        actual_secrets.update(block.get("aws_secretsmanager_secret", {}).keys())

    expected_secrets = set(spec["secrets"]["keys"])
    for key in expected_secrets - actual_secrets:
        failures.append(f"Missing Secrets Manager resource: {key}")

    return failures
