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
  name        = "sg-spec-demo"
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

  tags = { Name = "sg-spec-demo" }
}

resource "aws_instance" "eugenio" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.instance_type
  vpc_security_group_ids = [aws_security_group.sg_spec_demo.id]

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
