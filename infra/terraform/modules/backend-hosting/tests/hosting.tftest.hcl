mock_provider "aws" {
  mock_data "aws_iam_policy_document" {
    defaults = { json = "{\"Version\":\"2012-10-17\",\"Statement\":[]}" }
  }
  mock_data "aws_availability_zones" {
    defaults = { names = ["ap-south-1a", "ap-south-1b"] }
  }
}
variables {
  name           = "edip-production"
  region         = "ap-south-1"
  repository_url = "123456789012.dkr.ecr.ap-south-1.amazonaws.com/edip-production-backend"
  repository_arn = "arn:aws:ecr:ap-south-1:123456789012:repository/edip-production-backend"
  bucket_name    = "edip-test-artifacts"
  bucket_arn     = "arn:aws:s3:::edip-test-artifacts"
  model_bundle = {
    prefix              = "models/reviewed"
    model_version_id    = "model-version"
    metadata_version_id = "metadata-version"
    model_sha256        = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    metadata_sha256     = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
  }
}
run "public_boundary" {
  command = plan
  assert {
    condition     = aws_lb_listener.http.default_action[0].fixed_response[0].status_code == "403"
    error_message = "Unknown routes must fail closed at the ALB."
  }
  assert {
    condition     = toset(keys(aws_lb_listener_rule.public)) == toset(["/health", "/ready", "/docs", "/openapi.json"])
    error_message = "Only operational endpoints and Swagger schema may be public."
  }
  assert {
    condition     = alltrue([for rule in aws_lb_listener_rule.public : anytrue([for c in rule.condition : length(c.http_request_method) == 0 ? false : toset(c.http_request_method[0].values) == toset(["GET", "HEAD"])])])
    error_message = "Public routes must restrict request methods."
  }
  assert {
    condition     = aws_vpc_security_group_ingress_rule.task_alb.from_port == 8000 && aws_vpc_security_group_ingress_rule.task_alb.to_port == 8000 && aws_vpc_security_group_ingress_rule.task_alb.cidr_ipv4 == null
    error_message = "No public CIDR may directly access the task."
  }
  assert {
    condition     = aws_ecs_service.backend.desired_count == 0 && aws_ecs_service.backend.deployment_circuit_breaker[0].rollback
    error_message = "Bootstrap must not launch a placeholder image and rollback must be enabled."
  }
  assert {
    condition     = aws_lb_target_group.backend.health_check[0].path == "/ready"
    error_message = "Readiness must gate traffic."
  }
  assert {
    condition     = length(aws_subnet.public) == 2
    error_message = "ALB requires two public subnets."
  }
}
