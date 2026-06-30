from pathlib import Path

import hcl2


def _load_all_tf(base_dir: str) -> dict:
    merged: dict = {}
    for tf_file in Path(base_dir, "terraform").glob("*.tf"):
        try:
            with open(tf_file) as f:
                data = hcl2.load(f)
        except Exception:
            continue
        for key, value in data.items():
            merged.setdefault(key, [])
            merged[key].extend(value)
    return merged


def _load_raw_tf(base_dir: str) -> str:
    parts = []
    for tf_file in Path(base_dir, "terraform").glob("*.tf"):
        try:
            parts.append(tf_file.read_text())
        except Exception:
            pass
    return "\n".join(parts)


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
    raw = _load_raw_tf(base_dir)
    failures: list[str] = []

    # Region check
    expected_region = spec["infrastructure"]["region"]
    actual_region = _var_default(tf, "region")
    if actual_region != expected_region:
        failures.append(f"region: expected {expected_region}, found {actual_region}")

    # Instance type check
    expected_type = spec["infrastructure"]["instance_type"]
    actual_type = _var_default(tf, "instance_type")
    if actual_type != expected_type:
        failures.append(f"instance_type: expected {expected_type}, found {actual_type}")

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

    for port in sorted(expected_ports - actual_ports):
        failures.append(f"SG inbound port {port} not found in security group")

    # Secrets Manager resources
    actual_secrets: set[str] = set()
    for block in tf.get("resource", []):
        actual_secrets.update(block.get("aws_secretsmanager_secret", {}).keys())

    for key in set(spec["secrets"]["keys"]) - actual_secrets:
        failures.append(f"Missing Secrets Manager resource: {key}")

    # IAM checks
    iam_spec = spec.get("infrastructure", {}).get("iam")
    if iam_spec:
        expected_role = iam_spec.get("ec2_role")
        if expected_role and f'name = "{expected_role}"' not in raw:
            failures.append(f"IAM role '{expected_role}' not found in terraform")

        if "route53_update" in iam_spec.get("policies", []):
            if "route53:ChangeResourceRecordSets" not in raw:
                failures.append("IAM policy missing route53:ChangeResourceRecordSets")

        if "aws_iam_instance_profile" not in raw:
            failures.append("IAM instance profile (aws_iam_instance_profile) not found in terraform")

        if "iam_instance_profile" not in raw:
            failures.append("EC2 instance missing iam_instance_profile assignment")

    return failures
