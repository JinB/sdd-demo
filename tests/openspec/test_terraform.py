import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[2]))

from openspec.checks.terraform import check

SPEC = {
    "infrastructure": {
        "region": "eu-central-1",
        "instance_type": "t3.small",
        "security_group": {
            "name": "sdd-demo-sg",
            "inbound": [
                {"port": 22, "cidr": "0.0.0.0/0"},
                {"port": 80, "cidr": "0.0.0.0/0"},
                {"port": 443, "cidr": "0.0.0.0/0"},
            ],
        },
        "iam": {
            "ec2_role": "sdd-demo-ec2-role",
            "policies": ["route53_update"],
        },
    },
    "secrets": {"keys": ["db_password", "wp_admin_password", "gh_deploy_key"]},
}

VALID_TF = '''\
variable "region" {
  type    = string
  default = "eu-central-1"
}
variable "instance_type" {
  type    = string
  default = "t3.small"
}
resource "aws_security_group" "sg_spec_demo" {
  name = "sdd-demo-sg"
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
resource "aws_iam_role" "ec2_role" {
  name = "sdd-demo-ec2-role"
}
resource "aws_iam_role_policy" "route53_update" {
  name   = "sdd-demo-route53-update"
  policy = "route53:ChangeResourceRecordSets"
}
resource "aws_iam_instance_profile" "ec2_profile" {
  name = "sdd-demo-ec2-profile"
}
resource "aws_instance" "eugenio" {
  instance_type        = var.instance_type
  iam_instance_profile = aws_iam_instance_profile.ec2_profile.name
}
resource "aws_secretsmanager_secret" "db_password" {
  name = "sdd-demo/db_password"
}
resource "aws_secretsmanager_secret" "wp_admin_password" {
  name = "sdd-demo/wp_admin_password"
}
resource "aws_secretsmanager_secret" "gh_deploy_key" {
  name = "sdd-demo/gh_deploy_key"
}
'''


def test_valid_terraform_passes(tmp_path):
    (tmp_path / "terraform").mkdir()
    (tmp_path / "terraform" / "main.tf").write_text(VALID_TF)
    assert check(SPEC, base_dir=str(tmp_path)) == []


def test_wrong_region_fails(tmp_path):
    (tmp_path / "terraform").mkdir()
    (tmp_path / "terraform" / "main.tf").write_text(
        VALID_TF.replace('"eu-central-1"', '"us-east-1"')
    )
    failures = check(SPEC, base_dir=str(tmp_path))
    assert any("region" in f for f in failures)


def test_wrong_instance_type_fails(tmp_path):
    (tmp_path / "terraform").mkdir()
    (tmp_path / "terraform" / "main.tf").write_text(
        VALID_TF.replace('"t3.small"', '"t3.medium"')
    )
    failures = check(SPEC, base_dir=str(tmp_path))
    assert any("instance_type" in f for f in failures)


def test_missing_secret_fails(tmp_path):
    (tmp_path / "terraform").mkdir()
    tf = "\n".join(
        l for l in VALID_TF.splitlines() if "gh_deploy_key" not in l
    )
    (tmp_path / "terraform" / "main.tf").write_text(tf)
    failures = check(SPEC, base_dir=str(tmp_path))
    assert any("gh_deploy_key" in f for f in failures)


def test_missing_sg_port_fails(tmp_path):
    (tmp_path / "terraform").mkdir()
    tf = "\n".join(
        l for l in VALID_TF.splitlines()
        if "443" not in l
    )
    (tmp_path / "terraform" / "main.tf").write_text(tf)
    failures = check(SPEC, base_dir=str(tmp_path))
    assert any("443" in f for f in failures)


def test_missing_iam_role_fails(tmp_path):
    (tmp_path / "terraform").mkdir()
    tf = "\n".join(
        l for l in VALID_TF.splitlines()
        if "sdd-demo-ec2-role" not in l
    )
    (tmp_path / "terraform" / "main.tf").write_text(tf)
    failures = check(SPEC, base_dir=str(tmp_path))
    assert any("IAM role" in f for f in failures)


def test_missing_route53_policy_fails(tmp_path):
    (tmp_path / "terraform").mkdir()
    tf = "\n".join(
        l for l in VALID_TF.splitlines()
        if "ChangeResourceRecordSets" not in l
    )
    (tmp_path / "terraform" / "main.tf").write_text(tf)
    failures = check(SPEC, base_dir=str(tmp_path))
    assert any("route53" in f for f in failures)


def test_missing_instance_profile_fails(tmp_path):
    (tmp_path / "terraform").mkdir()
    tf = "\n".join(
        l for l in VALID_TF.splitlines()
        if "aws_iam_instance_profile" not in l and "iam_instance_profile" not in l
    )
    (tmp_path / "terraform" / "main.tf").write_text(tf)
    failures = check(SPEC, base_dir=str(tmp_path))
    assert any("instance profile" in f for f in failures)
