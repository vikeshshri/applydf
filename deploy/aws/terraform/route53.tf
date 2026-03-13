resource "aws_route53_zone" "main" {
  name = var.domain_name
}
}
resource "aws_route53_record" "api" {
resource "aws_route53_record" "api" {
  zone_id = aws_route53_zone.main.id
  name    = "api.${var.domain_name}"
  type    = "A"
  alias {
    name                   = aws_lb.api.dns_name
    zone_id                = aws_lb.api.zone_id
    evaluate_target_health = true
  }
}
  zone_id = aws_route53_zone.main.id
resource "aws_route53_record" "app" {
  zone_id = aws_route53_zone.main.id
  name    = "app.${var.domain_name}"
  type    = "A"
  alias {
    name                   = aws_cloudfront_distribution.frontend.domain_name
    zone_id                = "Z2FDTNDATAQYW2"
    evaluate_target_health = false
  }
}
  name    = "api.${var.domain_name}"
  type    = "A"
  ttl     = 300
  records = ["1.2.3.4"] # Replace with actual API LB IP
}
