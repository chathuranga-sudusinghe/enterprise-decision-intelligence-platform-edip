terraform {
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 6.0" }
  }
}
variable "name" { type = string }
variable "region" { type = string }
variable "repository_url" { type = string }
variable "repository_arn" { type = string }
variable "bucket_name" { type = string }
variable "bucket_arn" { type = string }
variable "model_bundle" {
  type = object({
    prefix              = string
    model_version_id    = string
    metadata_version_id = string
    model_sha256        = string
    metadata_sha256     = string
  })
  nullable = false
}
data "aws_availability_zones" "available" { state = "available" }
data "aws_caller_identity" "current" {}
data "aws_partition" "current" {}
locals {
  name = "${var.name}-backend"
}
resource "aws_vpc" "backend" {
  cidr_block           = "10.72.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true
  tags                 = { Name = var.name }
}
resource "aws_internet_gateway" "backend" {
  vpc_id = aws_vpc.backend.id
  tags   = { Name = var.name }
}
resource "aws_subnet" "public" {
  count             = 2
  vpc_id            = aws_vpc.backend.id
  cidr_block        = cidrsubnet(aws_vpc.backend.cidr_block, 8, count.index)
  availability_zone = sort(data.aws_availability_zones.available.names)[count.index]
  tags              = { Name = "${var.name}-public-${count.index}" }
}
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.backend.id
  tags   = { Name = "${var.name}-public" }
}
resource "aws_route" "internet" {
  route_table_id         = aws_route_table.public.id
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = aws_internet_gateway.backend.id
}
resource "aws_route_table_association" "public" {
  count          = 2
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}
resource "aws_security_group" "alb" {
  name        = "${var.name}-alb"
  description = "Temporary HTTP demo entry point"
  vpc_id      = aws_vpc.backend.id
}
resource "aws_security_group" "task" {
  name        = "${var.name}-task"
  description = "Backend accepts traffic only from EDIP ALB"
  vpc_id      = aws_vpc.backend.id
}
resource "aws_vpc_security_group_ingress_rule" "http" {
  security_group_id = aws_security_group.alb.id
  cidr_ipv4         = "0.0.0.0/0"
  from_port         = 80
  to_port           = 80
  ip_protocol       = "tcp"
}
resource "aws_vpc_security_group_egress_rule" "alb_task" {
  security_group_id            = aws_security_group.alb.id
  referenced_security_group_id = aws_security_group.task.id
  from_port                    = 8000
  to_port                      = 8000
  ip_protocol                  = "tcp"
}
resource "aws_vpc_security_group_ingress_rule" "task_alb" {
  security_group_id            = aws_security_group.task.id
  referenced_security_group_id = aws_security_group.alb.id
  from_port                    = 8000
  to_port                      = 8000
  ip_protocol                  = "tcp"
}
resource "aws_vpc_security_group_egress_rule" "task_https" {
  security_group_id = aws_security_group.task.id
  cidr_ipv4         = "0.0.0.0/0"
  from_port         = 443
  to_port           = 443
  ip_protocol       = "tcp"
}
resource "aws_lb" "backend" {
  name                       = substr(local.name, 0, 32)
  load_balancer_type         = "application"
  internal                   = false
  subnets                    = aws_subnet.public[*].id
  security_groups            = [aws_security_group.alb.id]
  drop_invalid_header_fields = true
}
resource "aws_lb_target_group" "backend" {
  name                 = substr(local.name, 0, 32)
  vpc_id               = aws_vpc.backend.id
  port                 = 8000
  protocol             = "HTTP"
  target_type          = "ip"
  deregistration_delay = 30
  health_check {
    path                = "/ready"
    matcher             = "200"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 3
  }
}
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.backend.arn
  port              = 80
  protocol          = "HTTP"
  default_action {
    type = "fixed-response"
    fixed_response {
      content_type = "text/plain"
      status_code  = "403"
      message_body = "Endpoint not publicly available."
    }
  }
}
# One exact path per rule: ALB limits each path condition to three values.
resource "aws_lb_listener_rule" "public" {
  for_each     = { "/health" = 10, "/ready" = 20, "/docs" = 30, "/openapi.json" = 40 }
  listener_arn = aws_lb_listener.http.arn
  priority     = each.value
  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.backend.arn
  }
  condition {
    path_pattern { values = [each.key] }
  }
  condition {
    http_request_method { values = ["GET", "HEAD"] }
  }
}
resource "aws_cloudwatch_log_group" "backend" {
  name              = "/ecs/${local.name}"
  retention_in_days = 7
}
data "aws_iam_policy_document" "task_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [data.aws_caller_identity.current.account_id]
    }
    condition {
      test     = "ArnLike"
      variable = "aws:SourceArn"
      values   = ["arn:${data.aws_partition.current.partition}:ecs:${var.region}:${data.aws_caller_identity.current.account_id}:*"]
    }
  }
}
resource "aws_iam_role" "execution" {
  name               = "${local.name}-execution"
  assume_role_policy = data.aws_iam_policy_document.task_assume.json
}
resource "aws_iam_role" "task" {
  name               = "${local.name}-task"
  assume_role_policy = data.aws_iam_policy_document.task_assume.json
}
data "aws_iam_policy_document" "execution" {
  statement {
    actions   = ["ecr:GetAuthorizationToken"]
    resources = ["*"]
  }
  statement {
    actions   = ["ecr:BatchCheckLayerAvailability", "ecr:GetDownloadUrlForLayer", "ecr:BatchGetImage"]
    resources = [var.repository_arn]
  }
  statement {
    actions   = ["logs:CreateLogStream", "logs:PutLogEvents"]
    resources = ["${aws_cloudwatch_log_group.backend.arn}:log-stream:ecs/backend/*"]
  }
}
resource "aws_iam_role_policy" "execution" {
  role   = aws_iam_role.execution.id
  name   = "runtime"
  policy = data.aws_iam_policy_document.execution.json
}
data "aws_iam_policy_document" "task" {
  dynamic "statement" {
    for_each = { "model.txt" = var.model_bundle.model_version_id, "metadata.json" = var.model_bundle.metadata_version_id }
    content {
      actions   = ["s3:GetObjectVersion"]
      resources = ["${var.bucket_arn}/${var.model_bundle.prefix}/${statement.key}"]
      condition {
        test     = "StringEquals"
        variable = "s3:VersionId"
        values   = [statement.value]
      }
    }
  }
}
resource "aws_iam_role_policy" "task" {
  role   = aws_iam_role.task.id
  name   = "model-read"
  policy = data.aws_iam_policy_document.task.json
}
resource "aws_ecs_cluster" "backend" {
  name = var.name
}
resource "aws_ecs_task_definition" "backend" {
  # DeregisterTaskDefinition cannot be ARN-scoped; retain revisions for reviewed cleanup.
  skip_destroy             = true
  family                   = local.name
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = "512"
  memory                   = "1024"
  execution_role_arn       = aws_iam_role.execution.arn
  task_role_arn            = aws_iam_role.task.arn
  runtime_platform {
    operating_system_family = "LINUX"
    cpu_architecture        = "X86_64"
  }
  container_definitions = jsonencode([{
    name = "backend"
    # Template only. CD substitutes an immutable digest before starting a task.
    image                  = "${var.repository_url}:unreleased"
    essential              = true
    user                   = "10001"
    readonlyRootFilesystem = true
    command                = ["python", "-m", "app.core.model_delivery"]
    portMappings           = [{ containerPort = 8000, protocol = "tcp" }]
    mountPoints            = [{ sourceVolume = "model", containerPath = "/models", readOnly = false }]
    environment = [for key, value in {
      APP_ENV                         = "production"
      ALLOWED_ORIGINS                 = "http://${aws_lb.backend.dns_name}"
      ALLOW_CREDENTIALS               = "false"
      EDIP_FAVORITA_MODEL_BUNDLE_PATH = "/models/favorita"
      EDIP_MODEL_BUCKET               = var.bucket_name
      EDIP_MODEL_PREFIX               = var.model_bundle.prefix
      EDIP_MODEL_VERSION_ID           = var.model_bundle.model_version_id
      EDIP_METADATA_VERSION_ID        = var.model_bundle.metadata_version_id
      EDIP_MODEL_SHA256               = var.model_bundle.model_sha256
      EDIP_METADATA_SHA256            = var.model_bundle.metadata_sha256
      AWS_DEFAULT_REGION              = var.region
      OMP_NUM_THREADS                 = "1"
    } : { name = key, value = value }]
    healthCheck = {
      command  = ["CMD-SHELL", "curl -fsS http://127.0.0.1:8000/ready || exit 1"]
      interval = 30, timeout = 5, retries = 3, startPeriod = 120
    }
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        awslogs-group         = aws_cloudwatch_log_group.backend.name
        awslogs-region        = var.region
        awslogs-stream-prefix = "ecs"
      }
    }
  }])
  volume { name = "model" }
}
resource "aws_ecs_service" "backend" {
  name                               = "backend"
  cluster                            = aws_ecs_cluster.backend.id
  task_definition                    = aws_ecs_task_definition.backend.arn
  desired_count                      = 0
  launch_type                        = "FARGATE"
  platform_version                   = "1.4.0"
  health_check_grace_period_seconds  = 180
  deployment_minimum_healthy_percent = 100
  deployment_maximum_percent         = 200
  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }
  network_configuration {
    subnets          = aws_subnet.public[*].id
    security_groups  = [aws_security_group.task.id]
    assign_public_ip = true
  }
  load_balancer {
    target_group_arn = aws_lb_target_group.backend.arn
    container_name   = "backend"
    container_port   = 8000
  }
  lifecycle { ignore_changes = [task_definition, desired_count] }
  depends_on = [aws_lb_listener_rule.public, aws_route.internet, aws_route_table_association.public, aws_iam_role_policy.execution, aws_iam_role_policy.task]
}
output "deployment" {
  value = {
    cluster            = aws_ecs_cluster.backend.name
    service            = aws_ecs_service.backend.name
    service_arn        = aws_ecs_service.backend.id
    template_arn       = aws_ecs_task_definition.backend.arn
    family_arn         = aws_ecs_task_definition.backend.arn_without_revision
    execution_role_arn = aws_iam_role.execution.arn
    task_role_arn      = aws_iam_role.task.arn
    model_bundle       = var.model_bundle
    bucket_name        = var.bucket_name
    repository_url     = var.repository_url
    url                = "http://${aws_lb.backend.dns_name}"
  }
}
output "alb_dns_name" { value = aws_lb.backend.dns_name }
