# Application Load Balancer for API
resource "aws_lb" "api" {
  name               = "api-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.ecs.id]
  subnets            = aws_subnet.public[*].id
}

# CloudFront Distribution for frontend
resource "aws_cloudfront_distribution" "frontend" {
    default_cache_behavior {
      allowed_methods  = ["GET", "HEAD", "OPTIONS"]
      cached_methods   = ["GET", "HEAD"]
      target_origin_id = "frontend-origin"
      viewer_protocol_policy = "redirect-to-https"
      forwarded_values {
        query_string = false
        cookies {
          forward = "none"
        }
      }
      min_ttl     = 0
      default_ttl = 3600
      max_ttl     = 86400
    }
  origin {
    domain_name = "example.com" # Replace with actual S3/static origin
    origin_id   = "frontend-origin"
  }
  enabled             = true
  is_ipv6_enabled     = true
  default_root_object = "index.html"
  price_class         = "PriceClass_All"
  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }
  viewer_certificate {
    cloudfront_default_certificate = true
  }
}
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
