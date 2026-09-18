variable "domain_name" {
  description = "Stable public DNS name for the EDIP backend."
  type        = string

  validation {
    condition     = can(regex("^[a-z0-9]([a-z0-9-]*[a-z0-9])?(\\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)+$", var.domain_name))
    error_message = "domain_name must be a lowercase fully qualified domain name."
  }
}

resource "aws_acm_certificate" "backend" {
  domain_name       = var.domain_name
  validation_method = "DNS"

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_acm_certificate_validation" "backend" {
  certificate_arn         = aws_acm_certificate.backend.arn
  validation_record_fqdns = toset([for option in aws_acm_certificate.backend.domain_validation_options : option.resource_record_name])
}

resource "aws_vpc_security_group_ingress_rule" "https" {
  security_group_id = aws_security_group.alb.id
  cidr_ipv4         = "0.0.0.0/0"
  from_port         = 443
  to_port           = 443
  ip_protocol       = "tcp"
}

resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.backend.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-2021-06"
  certificate_arn   = aws_acm_certificate_validation.backend.certificate_arn

  default_action {
    type = "fixed-response"

    fixed_response {
      content_type = "text/plain"
      status_code  = "403"
      message_body = "Endpoint not publicly available."
    }
  }
}

output "alb_zone_id" {
  value = aws_lb.backend.zone_id
}

output "acm_certificate_arn" {
  value = aws_acm_certificate.backend.arn
}

output "acm_dns_validation_records" {
  value = [
    for option in aws_acm_certificate.backend.domain_validation_options : {
      name  = option.resource_record_name
      type  = option.resource_record_type
      value = option.resource_record_value
    }
  ]
}
