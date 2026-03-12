variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "ecr_backend_repository" {
  description = "ECR backend repository name"
  type        = string
}

variable "ecr_frontend_repository" {
  description = "ECR frontend repository name"
  type        = string
}

# Add more variables for ECS, DB, VPC, etc.
