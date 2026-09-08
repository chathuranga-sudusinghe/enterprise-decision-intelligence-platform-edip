terraform {
  required_version = ">= 1.10.0, < 2.0.0"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 6.0" }
  }
  # Initially use -backend=false, then migrate this bootstrap state after the bucket exists.
  backend "s3" {}
}
