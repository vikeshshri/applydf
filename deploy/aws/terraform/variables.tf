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

variable "ecs_cluster_name" {
  description = "ECS cluster name"
  type        = string
}

variable "ecs_service_name" {
  description = "ECS service name"
  type        = string
}

variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
}

variable "public_subnet_cidrs" {
  description = "List of public subnet CIDRs"
  type        = list(string)
}

variable "db_name" {
  description = "Database name"
  type        = string
}

variable "db_user" {
  description = "Database user"
  type        = string
}

variable "db_password" {
  description = "Database password"
  type        = string
}

variable "domain_name" {
  description = "Root domain name"
  type        = string
}
