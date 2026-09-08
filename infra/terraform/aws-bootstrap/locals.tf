locals {
  plan_role_name      = coalesce(var.github_actions_plan_role_name, "${var.name_prefix}-${var.environment}-github-actions-terraform-plan")
  apply_role_name     = coalesce(var.github_actions_apply_role_name, "${var.name_prefix}-${var.environment}-github-actions-terraform-apply")
  backend_ecr_name    = coalesce(var.backend_ecr_repository_name, "${var.name_prefix}-${var.environment}-backend")
  frontend_ecr_name   = coalesce(var.frontend_ecr_repository_name, "${var.name_prefix}-${var.environment}-frontend")
  release_role_name   = coalesce(var.github_actions_release_role_name, "${var.name_prefix}-${var.environment}-github-actions-release")
  state_bucket_arn    = "arn:${data.aws_partition.current.partition}:s3:::${var.state_bucket_name}"
  artifact_bucket_arn = "arn:${data.aws_partition.current.partition}:s3:::${var.artifact_bucket_name}"
  state_object_arn    = "${local.state_bucket_arn}/${var.foundation_state_key}"
  lock_object_arn     = "${local.state_object_arn}.tflock"
  ecr_repository_arns = [for name in [local.backend_ecr_name, local.frontend_ecr_name] : "arn:${data.aws_partition.current.partition}:ecr:${var.aws_region}:${data.aws_caller_identity.current.account_id}:repository/${name}"]
  release_role_arn    = "arn:${data.aws_partition.current.partition}:iam::${data.aws_caller_identity.current.account_id}:role/${local.release_role_name}"
  common_tags         = merge({ Environment = var.environment, ManagedBy = "Terraform", Project = var.name_prefix, Purpose = "TerraformBootstrap" }, var.additional_tags)
}
