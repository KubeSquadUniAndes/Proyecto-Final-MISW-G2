provider "aws" {
  region  = var.region
  profile = var.aws_profile != "" ? var.aws_profile : null
}
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}