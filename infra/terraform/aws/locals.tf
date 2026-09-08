locals {
  backend_ecr_repository_name      = coalesce(var.backend_ecr_repository_name, "${var.name_prefix}-${var.environment}-backend")
  frontend_ecr_repository_name     = coalesce(var.frontend_ecr_repository_name, "${var.name_prefix}-${var.environment}-frontend")
  github_actions_release_role_name = coalesce(var.github_actions_release_role_name, "${var.name_prefix}-${var.environment}-github-actions-release")
  ecr_repository_names = {
    backend  = local.backend_ecr_repository_name
    frontend = local.frontend_ecr_repository_name
  }
  common_tags = merge({ Environment = var.environment, ManagedBy = "Terraform", Project = var.name_prefix }, var.additional_tags)
}
