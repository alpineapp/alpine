terraform {
  backend "s3" {
    bucket         = "alpineapp-tfstate"
    key            = "alpineapp-tfstate.tfstate"
    region         = "ap-southeast-1"
    encrypt        = true
    dynamodb_table = "alpineapp-tfstate-tfstate-lock"
  }
}

provider "aws" {
  region  = "ap-southeast-1"
}

locals {
  prefix = "${var.prefix}-${terraform.workspace}"
  common_tags = {
    Environment = terraform.workspace
    Project     = var.project
    Owner       = var.contact
    ManagedBy   = "Terraform"
  }
}

data "aws_region" "current" {} # so we don't need to hardcode the region in other files