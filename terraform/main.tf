terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.4"
    }
  }
}

provider "aws" {
  region  = var.aws_region
  profile = "default"

}

resource "random_password" "password" {
  length           = 16
  special          = true
  override_special = "!#$%&*()-_=+[]{}<>:?"
}

data "aws_vpc" "default" {
  default = true
}

# security groups
resource "aws_security_group" "security-group-us-east-2-d-postgres" {
  vpc_id      = data.aws_vpc.default.id
  name        = "security-group-us-east-2-d-postgres"
  description = "Allow all inbound for Postgres"
  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "security-group-us-east-2-d-ssh" {
  name        = "security-group-us-east-2-d-ssh"
  description = "Security group to allow inbound SSH connections"

  ingress {
    description = "Inbound SCP"
    from_port   = 22
    to_port     = 22
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

# Fetch the latest Ubuntu 20.04 AMI
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical
  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }
}

# Create EC2 with IAM role to allow EMR, Redshift, & S3 access and security group
resource "tls_private_key" "custom_key" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

resource "aws_key_pair" "generated_key" {
  key_name_prefix = var.key_name
  public_key      = tls_private_key.custom_key.public_key_openssh
}

resource "aws_instance" "default" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = "t3.micro"
  key_name      = aws_key_pair.generated_key.key_name
  vpc_security_group_ids = [
    aws_security_group.security-group-us-east-2-d-ssh.id
  ]
  tags = {
    Project = "shouldishovel"
    Name    = "app.dev.us-east-2.aws.shouldishovel.com"
  }
}


resource "aws_db_instance" "default" {
  allocated_storage = 50
  db_name           = "mydb"
  engine            = "postgres"
  engine_version    = "13.7"
  instance_class    = "db.t3.micro"
  username          = "myn"
  password          = random_password.password.result
  vpc_security_group_ids = [
    aws_security_group.security-group-us-east-2-d-postgres.id
  ]
  skip_final_snapshot = true
  publicly_accessible = true
  tags = {
    Project = "shouldishovel"
    Name    = "sql01.dev.us-east-2.aws.shouldishovel.com"
  }
}
