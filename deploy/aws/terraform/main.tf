provider "aws" {
  region = var.aws_region
}

resource "aws_ecr_repository" "backend" {
  name = var.ecr_backend_repository
}

resource "aws_ecr_repository" "frontend" {
  name = var.ecr_frontend_repository
}

# Add ECS, DB, VPC, etc. resources here as needed
