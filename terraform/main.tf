terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.region
}

data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"]
  }
}

resource "aws_security_group" "sg_spec_demo" {
  name        = "sdd-demo-sg"
  description = "sdd-demo security group"

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

  tags = { Name = "sdd-demo-sg" }
}

resource "aws_iam_role" "ec2_role" {
  name = "sdd-demo-ec2-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
    }]
  })

  tags = { Name = "sdd-demo-ec2-role" }
}

resource "aws_iam_role_policy" "route53_update" {
  name = "sdd-demo-route53-update"
  role = aws_iam_role.ec2_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "route53:GetChange",
        "route53:ChangeResourceRecordSets",
        "route53:ListHostedZones",
        "route53:ListHostedZonesByName",
        "route53:ListResourceRecordSets"
      ]
      Resource = "*"
    }]
  })
}

resource "aws_iam_instance_profile" "ec2_profile" {
  name = "sdd-demo-ec2-profile"
  role = aws_iam_role.ec2_role.name
}

resource "aws_instance" "eugenio" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.instance_type
  vpc_security_group_ids = [aws_security_group.sg_spec_demo.id]
  iam_instance_profile   = aws_iam_instance_profile.ec2_profile.name

  tags = { Name = "sdd-demo" }
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
