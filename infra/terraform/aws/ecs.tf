# =========================================================
# CloudWatch log group for ECS application logs
# =========================================================
resource "aws_cloudwatch_log_group" "api" {
  name              = "/ecs/${local.name_prefix}-api"
  retention_in_days = 14
}

# =========================================================
# ECS cluster
# =========================================================
resource "aws_ecs_cluster" "main" {
  name = "${local.name_prefix}-cluster"

  tags = {
    Name = "${local.name_prefix}-cluster"
  }
}

# =========================================================
# ECS task definition
# Uses ECR image and injects app environment variables
# =========================================================
resource "aws_ecs_task_definition" "api" {
  family                   = "${local.name_prefix}-api"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = tostring(var.ecs_task_cpu)
  memory                   = tostring(var.ecs_task_memory)
  execution_role_arn       = aws_iam_role.ecs_execution_role.arn
  task_role_arn            = aws_iam_role.ecs_task_role.arn

  container_definitions = jsonencode([
    {
      name      = "api"
      image     = "${aws_ecr_repository.api.repository_url}:${var.app_image_tag}"
      essential = true

      portMappings = [
        {
          containerPort = var.container_port
          hostPort      = var.container_port
          protocol      = "tcp"
        }
      ]

      environment = [
        { name = "APP_NAME", value = var.app_name },
        { name = "APP_VERSION", value = var.app_version },
        { name = "APP_ENV", value = var.app_env },
        { name = "API_HOST", value = var.api_host },
        { name = "API_PORT", value = tostring(var.api_port) },
        { name = "ALLOW_CREDENTIALS", value = tostring(var.allow_credentials) },
        { name = "ALLOWED_ORIGINS", value = var.allowed_origins },
        { name = "OPENAI_API_KEY", value = var.openai_api_key },
        { name = "PINECONE_API_KEY", value = var.pinecone_api_key },
        { name = "PINECONE_INDEX_NAME", value = var.pinecone_index_name },
        { name = "PINECONE_NAMESPACE", value = var.pinecone_namespace },
        { name = "OPENAI_EMBED_MODEL", value = var.openai_embed_model },
        { name = "OPENAI_CHAT_MODEL", value = var.openai_chat_model },
        { name = "RAG_TOP_K", value = tostring(var.rag_top_k) },
        { name = "RAG_MAX_CONTEXT_CHARS", value = tostring(var.rag_max_context_chars) }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.api.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "ecs"
        }
      }
    }
  ])

  tags = {
    Name = "${local.name_prefix}-api-task"
  }
}

# =========================================================
# ECS service
# Phase 1 uses public subnets with public IP for simplicity
# =========================================================
resource "aws_ecs_service" "api" {
  name            = "${local.name_prefix}-api-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.api.arn
  desired_count   = var.desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = aws_subnet.public[*].id
    security_groups  = [aws_security_group.ecs_service.id]
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.api.arn
    container_name   = "api"
    container_port   = var.container_port
  }

  depends_on = [
    aws_lb_listener.http
  ]

  tags = {
    Name = "${local.name_prefix}-api-service"
  }
}