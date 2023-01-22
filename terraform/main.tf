resource "random_password" "password" {
  length           = 16
  special          = true
  override_special = "!#$%&*()-_=+[]{}<>:?"
}

data "aws_vpc" "default" {
  default = true
}

# static IP
resource "aws_eip" "ip" {
  instance = aws_instance.default.id
}

# security groups
# resource "aws_security_group" "security-group-us-east-2-d-postgres" {
#   vpc_id      = data.aws_vpc.default.id
#   name        = "security-group-us-east-2-d-postgres"
#   description = "Allow all inbound for Postgres"
#   ingress {
#     from_port   = 5432
#     to_port     = 5432
#     protocol    = "tcp"
#     cidr_blocks = ["0.0.0.0/0"]
#   }
#   egress {
#     from_port   = 80
#     to_port     = 80
#     protocol    = "tcp"
#     cidr_blocks = ["0.0.0.0/0"]
#   }
#   egress {
#     from_port   = 443
#     to_port     = 443
#     protocol    = "tcp"
#     cidr_blocks = ["0.0.0.0/0"]
#   }
# }

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

  ingress {
    description = "Inbound SCP"
    from_port   = 80
    to_port     = 80
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
  user_data = templatefile("aws_instance.default.tftpl", {
    AWS_RDS_PASSWORD      = var.AWS_RDS_PASSWORD,
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


# resource "aws_db_instance" "default" {
#   allocated_storage = 50
#   db_name           = "mydb"
#   engine            = "postgres"
#   engine_version    = "13.7"
#   instance_class    = "db.t3.micro"
#   username          = "myn"
#   password          = var.AWS_RDS_PASSWORD
#   vpc_security_group_ids = [
#     aws_security_group.security-group-us-east-2-d-postgres.id
#   ]
#   skip_final_snapshot = true
#   publicly_accessible = true
# }

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

# resource "aws_iam_role" "rds_role" {
#   name = "rds_role"

#   # Terraform's "jsonencode" function converts a
#   # Terraform expression result to valid JSON syntax.
#   assume_role_policy = jsonencode({
#     Version = "2012-10-17"
#     Statement = [
#       {
#         Action = "sts:AssumeRole"
#         Effect = "Allow"
#         Sid    = ""
#         Principal = {
#           Service = "rds.amazonaws.com"
#         }
#       },
#     ]
#   })
# }
# resource "aws_iam_policy" "s3-access" {
#   name        = "rds-s3-import-policy"
#   path        = "/"
#   description = "RDS to S3 import policy"

#   policy = jsonencode({
#     "Version" : "2012-10-17",
#     "Statement" : [
#       {
#         "Sid" : "s3import",
#         "Action" : [
#           "s3:GetObject",
#           "s3:ListBucket"
#         ],
#         "Effect" : "Allow",
#         "Resource" : [
#           "arn:aws:s3:::sto01.dev.us-east-2.aws.shouldishovel.com",
#           "arn:aws:s3:::sto01.dev.us-east-2.aws.shouldishovel.com/*"
#         ]
#       }
#     ]
#   })
# }

# resource "aws_iam_role_policy_attachment" "rds-to-s3" {
#   role       = aws_iam_role.rds_role.name
#   policy_arn = aws_iam_policy.s3-access.arn
# }

# resource "aws_db_instance_role_association" "rds_s3import_role" {
#   db_instance_identifier = aws_db_instance.default.id
#   feature_name           = "s3Import"
#   role_arn               = aws_iam_role.rds_role.arn
# }
