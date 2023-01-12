## Key to allow connection to our EC2 instance
variable "key_name" {
  description = "EC2 key name"
  type        = string
  default     = "app-key"
}

## EC2 instance type
variable "instance_type" {
  description = "Instance type for EMR and EC2"
  type        = string
  default     = "t3.micro"
}

## Alert email receiver
variable "alert_email_id" {
  description = "Email id to send alerts to "
  type        = string
  default     = "mynhardt+shouldishovel@gmail.com"
}

# Terraform cloud defined variable
variable "AWS_RDS_PASSWORD" {
  description = "AWS_RDS_PASSWORD"
  type        = string
}

# Terraform cloud defined variable
variable "GOOGLE_API_KEY" {
  description = "GOOGLE_API_KEY"
  type        = string
}

variable "AWS_SECRET_ACCESS_KEY" {
  description = "AWS_SECRET_ACCESS_KEY"
  type        = string
}

variable "AWS_ACCESS_KEY_ID" {
  description = "AWS_ACCESS_KEY_ID"
  type        = string
}

variable "AWS_DEFAULT_REGION" {
  description = "AWS_DEFAULT_REGION"
  type        = string
}

variable "website_domain" {
  type    = string
  default = "shouldishovel.com"
}

variable "repo_url" {
  description = "Repository url to clone into production machine"
  type        = string
  default     = "https://github.com/mynhardtburger/should-i-shovel.git"
}
