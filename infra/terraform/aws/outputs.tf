output "aws_region" {
  description = "AWS region used by this deployment."
  value       = var.aws_region
}

output "vpc_id" {
  description = "Main VPC ID."
  value       = aws_vpc.main.id
}

output "public_subnet_ids" {
  description = "Public subnet IDs."
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "Private subnet IDs."
  value       = aws_subnet.private[*].id
}

output "ecr_repository_name" {
  description = "ECR repository name for the API image."
  value       = aws_ecr_repository.api.name
}

output "ecr_repository_url" {
  description = "ECR repository URL for docker push."
  value       = aws_ecr_repository.api.repository_url
}

output "ecs_cluster_name" {
  description = "ECS cluster name."
  value       = aws_ecs_cluster.main.name
}

output "ecs_service_name" {
  description = "ECS service name."
  value       = aws_ecs_service.api.name
}

output "alb_dns_name" {
  description = "Public ALB DNS name."
  value       = aws_lb.api.dns_name
}

output "api_base_url" {
  description = "Base URL for the deployed API."
  value       = "http://${aws_lb.api.dns_name}"
}