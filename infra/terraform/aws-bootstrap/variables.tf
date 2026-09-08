variable "aws_region" {
  description = "AWS region for bootstrap resources."
  type        = string
}
variable "name_prefix" {
  description = "Resource prefix."
  type        = string
  default     = "edip"
}
variable "environment" {
  description = "Environment."
  type        = string
  default     = "production"
}
variable "state_bucket_name" {
  description = "Dedicated Terraform state bucket name."
  type        = string
}
variable "artifact_bucket_name" {
  description = "Separate application artifact bucket name used for IAM scoping."
  type        = string
}
variable "bootstrap_state_key" {
  description = "Bootstrap root state object key used after migration."
  type        = string
  default     = "bootstrap/terraform.tfstate"
  validation {
    condition     = length(trimspace(var.bootstrap_state_key)) > 0 && !startswith(var.bootstrap_state_key, "/") && !endswith(var.bootstrap_state_key, ".tflock")
    error_message = "Use a non-empty bootstrap key without a leading slash or .tflock suffix."
  }
}
variable "foundation_state_key" {
  description = "Main foundation state object key."
  type        = string
  validation {
    condition     = length(trimspace(var.foundation_state_key)) > 0 && !startswith(var.foundation_state_key, "/") && !endswith(var.foundation_state_key, ".tflock")
    error_message = "Use a non-empty key without a leading slash or .tflock suffix."

  }
}
variable "github_oidc_provider_arn" {
  description = "ARN of the existing shared account-level GitHub Actions IAM OIDC provider."
  type        = string
  validation {
    condition     = can(regex("^arn:[^:]+:iam::[0-9]{12}:oidc-provider/token\\.actions\\.githubusercontent\\.com$", trimspace(var.github_oidc_provider_arn)))
    error_message = "github_oidc_provider_arn must be the ARN of the shared token.actions.githubusercontent.com IAM OIDC provider."
  }
}
variable "github_actions_plan_role_name" {
  description = "Plan role override."
  type        = string
  default     = null
}
variable "github_actions_apply_role_name" {
  description = "Apply role override."
  type        = string
  default     = null
}
variable "github_actions_plan_oidc_subjects" {
  description = "Exact plan OIDC subjects."
  type        = set(string)
  validation {
    condition     = length(var.github_actions_plan_oidc_subjects) > 0 && alltrue([for s in var.github_actions_plan_oidc_subjects : can(regex("^repo:[^:*?]+/[^:*?]+:(pull_request|ref:refs/(heads|tags)/[^*?]+|environment:[^*?]+)$", s))])
    error_message = "Plan subjects must be exact and contain no wildcards."

  }
}
variable "github_actions_apply_oidc_subjects" {
  description = "Exact protected-environment apply OIDC subjects."
  type        = set(string)
  validation {
    condition     = length(var.github_actions_apply_oidc_subjects) > 0 && alltrue([for s in var.github_actions_apply_oidc_subjects : can(regex("^repo:[^:*?]+/[^:*?]+:environment:[^*?]+$", s))])
    error_message = "Apply subjects must be exact protected-environment subjects."

  }
}
variable "backend_ecr_repository_name" {
  description = "Backend ECR name override."
  type        = string
  default     = null
}
variable "frontend_ecr_repository_name" {
  description = "Frontend ECR name override."
  type        = string
  default     = null
}
variable "github_actions_release_role_name" {
  description = "Release role name override."
  type        = string
  default     = null
}
variable "additional_tags" {
  description = "Additional tags."
  type        = map(string)
  default     = {}
}
