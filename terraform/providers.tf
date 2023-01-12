terraform {
  cloud {
    organization = "mynhardt"
    workspaces {
      name = "should-i-shovel"
    }
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.20.0"
    }

    # awscc = {
    #   source  = "hashicorp/awscc"
    #   version = ">=0.36.0"
    # }

    docker = {
      source  = "kreuzwerker/docker"
      version = "2.25.0"
    }
  }
}

provider "aws" {
  region     = var.AWS_DEFAULT_REGION
  access_key = var.AWS_ACCESS_KEY_ID
  secret_key = var.AWS_SECRET_ACCESS_KEY
  default_tags {
    tags = {
      Project = "shouldishovel"
    }
  }
}

# provider "awscc" {
#   region = var.aws_region
# }

provider "docker" {}
