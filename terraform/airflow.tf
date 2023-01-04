# # Based off this example https://github.com/aws-ia/terraform-aws-mwaa/blob/main/examples/basic/main.tf

# data "aws_availability_zones" "available" {}

# data "aws_caller_identity" "current" {}

# locals {
#   azs         = slice(data.aws_availability_zones.available.names, 0, 2)
#   bucket_name = format("%s-%s", "aws-ia-mwaa", data.aws_caller_identity.current.account_id)
# }

# #-----------------------------------------------------------
# # Create an S3 bucket and upload sample DAG
# #-----------------------------------------------------------
# resource "aws_s3_bucket" "this" {
#   bucket = local.bucket_name
# }

# resource "aws_s3_bucket_acl" "this" {
#   bucket = aws_s3_bucket.this.id
#   acl    = "private"
# }

# resource "aws_s3_bucket_versioning" "this" {
#   bucket = aws_s3_bucket.this.id
#   versioning_configuration {
#     status = "Enabled"
#   }
# }

# resource "aws_s3_bucket_server_side_encryption_configuration" "this" {
#   bucket = aws_s3_bucket.this.id

#   rule {
#     apply_server_side_encryption_by_default {
#       sse_algorithm = "AES256"
#     }
#   }
# }

# resource "aws_s3_bucket_public_access_block" "this" {
#   bucket                  = aws_s3_bucket.this.id
#   block_public_acls       = true
#   block_public_policy     = true
#   ignore_public_acls      = true
#   restrict_public_buckets = true
# }

# # Upload DAGS
# resource "aws_s3_object" "object1" {
#   for_each = fileset("../dags/", "*")
#   bucket   = aws_s3_bucket.this.id
#   key      = "dags/${each.value}"
#   source   = "dags/${each.value}"
#   etag     = filemd5("../dags/${each.value}")
# }

# # Upload plugins/requirements.txt
# resource "aws_s3_object" "reqs" {
#   for_each = fileset("../aws-mwaa/", "*")
#   bucket   = aws_s3_bucket.this.id
#   key      = each.value
#   source   = "mwaa/${each.value}"
#   etag     = filemd5("../configs/aws-mwaa/${each.value}")
# }

# #-----------------------------------------------------------
# # NOTE: MWAA Airflow environment takes minimum of 20 mins
# #-----------------------------------------------------------
# module "mwaa" {
#   source  = "aws-ia/mwaa/aws"
#   version = "0.0.1"

#   name              = "basic-mwaa"
#   airflow_version   = "2.2.2"
#   environment_class = "mw1.small"
#   create_s3_bucket  = false
#   source_bucket_arn = aws_s3_bucket.this.arn
#   dag_s3_path       = "dags"

#   ## If uploading requirements.txt or plugins, you can enable these via these options
#   #plugins_s3_path      = "plugins.zip"
#   #   requirements_s3_path = "requirements.txt"

#   min_workers        = 1
#   max_workers        = 2
#   vpc_id             = module.vpc.vpc_id
#   private_subnet_ids = module.vpc.private_subnets

#   webserver_access_mode = "PUBLIC_ONLY" # Default PRIVATE_ONLY for production environments

#   logging_configuration = {
#     dag_processing_logs = {
#       enabled   = true
#       log_level = "INFO"
#     }

#     scheduler_logs = {
#       enabled   = true
#       log_level = "INFO"
#     }

#     task_logs = {
#       enabled   = true
#       log_level = "INFO"
#     }

#     webserver_logs = {
#       enabled   = true
#       log_level = "INFO"
#     }

#     worker_logs = {
#       enabled   = true
#       log_level = "INFO"
#     }
#   }

#   airflow_configuration_options = {
#     "core.load_default_connections" = "false"
#     "core.load_examples"            = "false"
#     "webserver.dag_default_view"    = "tree"
#     "webserver.dag_orientation"     = "TB"
#     "logging.logging_level"         = "INFO"
#   }
# }