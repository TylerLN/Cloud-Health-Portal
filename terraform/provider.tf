// Set up AWS provider and version requirements.
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }

  required_version = ">= 1.2"
}

provider "aws" {
  region = "us-west-2"
}