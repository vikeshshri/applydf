resource "aws_route53_zone" "main" {
  name = var.domain_name
}

resource "aws_route53_record" "api" {
  zone_id = aws_route53_zone.main.id
  name    = "api.${var.domain_name}"
  type    = "A"
  ttl     = 300
  records = ["1.2.3.4"] # Replace with actual API LB IP
}
