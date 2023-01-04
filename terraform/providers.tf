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

    # docker = {
    #   source  = "kreuzwerker/docker"
    #   version = "2.24.0"
    # }
  }
}


# AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY are setup within terraform cloud as environmental variables.
provider "aws" {
  region = var.aws_region
  default_tags {
    tags = {
      Project = "shouldishovel"
    }
  }
}

# provider "awscc" {
#   region = var.aws_region
# }

# provider "docker" {}
