output "aws_region" {
  description = "Region set for AWS"
  value       = var.aws_region
}

output "ec2_public_dns" {
  description = "EC2 public dns."
  value       = aws_instance.default.public_dns
}

output "private_key" {
  description = "EC2 private key."
  value       = tls_private_key.custom_key.private_key_pem
  sensitive   = true
}

output "public_key" {
  description = "EC2 public key."
  value       = tls_private_key.custom_key.public_key_openssh
}

output "db_endpoint" {
  value       = aws_db_instance.default.endpoint
  description = "The database endpoint."
  sensitive   = false
}

output "db_name" {
  value       = aws_db_instance.default.db_name
  description = "The database name."
  sensitive   = false
}

output "db_user" {
  value       = aws_db_instance.default.username
  description = "The database user."
  sensitive   = false
}

output "db_password" {
  value       = aws_db_instance.default.password
  description = "The database password."
  sensitive   = true
}
