variable "aws_region" {
  description = "AWS region for the EDIP foundation resources."
  type        = string
  validation {
    condition     = length(trimspace(var.aws_region)) > 0 && !strcontains(var.aws_region, " ")
    error_message = "aws_region must be non-empty and contain no spaces."
  }
}
variable "name_prefix" {
  description = "Prefix for derived resource names."
  type        = string
  default     = "edip"
  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9-]{1,30}[a-z0-9]$", var.name_prefix))
    error_message = "name_prefix must be 3-32 lowercase alphanumeric or hyphen characters."
  }
}
variable "environment" {
  description = "Environment used in names and tags."
  type        = string
  default     = "production"
  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9-]{1,18}[a-z0-9]$", var.environment))
    error_message = "environment must be 3-20 lowercase alphanumeric or hyphen characters."
  }
}
variable "backend_ecr_repository_name" {
  description = "Optional backend ECR repository name override."
  type        = string
  default     = null
  validation {
    condition     = var.backend_ecr_repository_name == null ? true : can(regex("^[a-z0-9]+([._/-][a-z0-9]+)*$", var.backend_ecr_repository_name))
    error_message = "backend_ecr_repository_name must be a valid private ECR repository name."
  }
}
variable "frontend_ecr_repository_name" {
  description = "Optional frontend ECR repository name override."
  type        = string
  default     = null
  validation {
    condition     = var.frontend_ecr_repository_name == null ? true : can(regex("^[a-z0-9]+([._/-][a-z0-9]+)*$", var.frontend_ecr_repository_name))
    error_message = "frontend_ecr_repository_name must be a valid private ECR repository name."
  }
}
variable "artifact_bucket_name" {
  description = "Globally unique S3 bucket name for approved model bundles and release artifacts."
  type        = string
  validation {
    condition     = length(var.artifact_bucket_name) >= 3 && length(var.artifact_bucket_name) <= 63 && can(regex("^[a-z0-9][a-z0-9.-]*[a-z0-9]$", var.artifact_bucket_name)) && !strcontains(var.artifact_bucket_name, "..") && !strcontains(var.artifact_bucket_name, ".-") && !strcontains(var.artifact_bucket_name, "-.") && !can(regex("^([0-9]{1,3}\\.){3}[0-9]{1,3}$", var.artifact_bucket_name))
    error_message = "artifact_bucket_name must satisfy S3 general purpose bucket naming rules."
  }
}
variable "github_actions_release_role_name" {
  description = "Optional GitHub Actions release IAM role name override."
  type        = string
  default     = null
  validation {
    condition     = var.github_actions_release_role_name == null ? true : can(regex("^[A-Za-z0-9+=,.@_-]{1,64}$", var.github_actions_release_role_name))
    error_message = "github_actions_release_role_name must be a valid IAM role name."
  }
}
variable "github_actions_release_oidc_subjects" {
  description = "Exact GitHub OIDC subjects allowed to assume the role; wildcards are rejected."
  type        = set(string)
  validation {
    condition     = length(var.github_actions_release_oidc_subjects) > 0 && alltrue([for subject in var.github_actions_release_oidc_subjects : can(regex("^repo:[^:*?]+/[^:*?]+:(ref:refs/(heads|tags)/[^*?]+|environment:[^*?]+)$", subject))])
    error_message = "Use exact repository branch, tag, or environment OIDC subjects without wildcards."
  }
}
variable "ecr_untagged_image_expiration_days" {
  description = "Days before untagged ECR images expire."
  type        = number
  default     = 30
  validation {
    condition     = var.ecr_untagged_image_expiration_days >= 1
    error_message = "Must be at least 1."
  }
}
variable "multipart_upload_expiration_days" {
  description = "Days before incomplete S3 multipart uploads are aborted."
  type        = number
  default     = 7
  validation {
    condition     = var.multipart_upload_expiration_days >= 1
    error_message = "Must be at least 1."
  }
}
variable "additional_tags" {
  description = "Additional tags for taggable resources."
  type        = map(string)
  default     = {}
}
