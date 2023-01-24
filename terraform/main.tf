# static IP
resource "aws_eip" "ip" {
  instance = aws_instance.default.id
  vpc      = true
}

resource "aws_vpc" "default" {
  cidr_block = var.vpc_cidr
}

resource "aws_subnet" "public_subnet" {
  vpc_id                  = aws_vpc.default.id
  cidr_block              = var.public_subnet_cidr
  map_public_ip_on_launch = true
  availability_zone       = "${var.AWS_DEFAULT_REGION}a"
}

resource "aws_internet_gateway" "default" {
  vpc_id = aws_vpc.default.id
}

resource "aws_route_table" "default" {
  vpc_id = aws_vpc.default.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.default.id
  }
}

resource "aws_route_table_association" "default" {
  subnet_id      = aws_subnet.public_subnet.id
  route_table_id = aws_route_table.default.id
}

resource "aws_security_group" "security-group-us-east-2-d-ssh_http" {
  name        = "security-group-us-east-2-d-ssh_http"
  description = "Security group to allow inbound SSH & HTTP/S connections"
  vpc_id      = aws_vpc.default.id

  ingress {
    description = "Inbound SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  ingress {
    description = "Inbound http"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  ingress {
    description = "Inbound http"
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
  instance_type = var.instance_type
  key_name      = aws_key_pair.generated_key.key_name
  subnet_id     = aws_subnet.public_subnet.id
  vpc_security_group_ids = [
    aws_security_group.security-group-us-east-2-d-ssh_http.id
  ]
  user_data = templatefile("aws_instance.default.tftpl", {
    AWS_RDS_PASSWORD      = "mysecretpassword",
    AWS_RDS_HOST          = "postgis",
    AWS_RDS_DB            = "postgres",
    AWS_RDS_USER          = "postgres",
    AWS_RDS_PORT          = 5432,
    GOOGLE_API_KEY        = var.GOOGLE_API_KEY,
    AWS_ACCESS_KEY_ID     = var.AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY = var.AWS_SECRET_ACCESS_KEY,
    AWS_DEFAULT_REGION    = var.AWS_DEFAULT_REGION,
    AWS_BUCKET            = aws_s3_bucket.s3_gribs.bucket,
    REPO_URL              = var.repo_url
  })
}


resource "aws_s3_bucket" "s3_gribs" {
  bucket = "sto01.dev.us-east-2.aws.shouldishovel.com"
}

resource "aws_s3_bucket_acl" "s3_gribs" {
  bucket = aws_s3_bucket.s3_gribs.id
  acl    = "private"
}

resource "aws_s3_bucket_versioning" "s3_gribs" {
  bucket = aws_s3_bucket.s3_gribs.id
  versioning_configuration {
    status = "Disabled"
  }
}
