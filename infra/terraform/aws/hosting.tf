variable "hosting_enabled" {
  description = "Enable the temporary backend research/demo hosting stack."
  type        = bool
  default     = false
}
variable "model_bundle" {
  description = "Reviewed S3 prefix, immutable object versions and SHA-256 hashes."
  type = object({
    prefix              = string
    model_version_id    = string
    metadata_version_id = string
    model_sha256        = string
    metadata_sha256     = string
  })
  default = null
  validation {
    condition = var.model_bundle == null ? true : (
      can(regex("^[A-Za-z0-9/_-]+$", var.model_bundle.prefix)) &&
      !startswith(var.model_bundle.prefix, "/") && !endswith(var.model_bundle.prefix, "/") &&
      alltrue([for v in [var.model_bundle.model_version_id, var.model_bundle.metadata_version_id] : length(v) > 0 && v != "null"]) &&
      alltrue([for h in [var.model_bundle.model_sha256, var.model_bundle.metadata_sha256] : can(regex("^[a-f0-9]{64}$", h))])
    )
    error_message = "Use an explicit prefix, non-null S3 version IDs and lowercase SHA-256 hashes."
  }
}
module "hosting" {
  count          = var.hosting_enabled ? 1 : 0
  source         = "../modules/backend-hosting"
  name           = "${var.name_prefix}-${var.environment}"
  region         = var.aws_region
  repository_url = aws_ecr_repository.application["backend"].repository_url
  repository_arn = aws_ecr_repository.application["backend"].arn
  bucket_name    = aws_s3_bucket.artifacts.bucket
  bucket_arn     = aws_s3_bucket.artifacts.arn
  model_bundle   = var.model_bundle
  domain_name    = "edip.vora-technologies.com"
}
output "application_hosting" {
  description = "Deployment contract; null until hosting is enabled."
  value       = var.hosting_enabled ? merge(module.hosting[0].deployment, { release_role_arn = aws_iam_role.github_actions_release.arn }) : null
}
output "public_application_url" {
  value = var.hosting_enabled ? module.hosting[0].deployment.url : null
}
output "alb_dns_name" {
  value = var.hosting_enabled ? module.hosting[0].alb_dns_name : null
}
output "cloudwatch_dashboard_name" {
  description = "CloudWatch operations dashboard name; null until hosting is enabled."
  value       = var.hosting_enabled ? module.hosting[0].cloudwatch_dashboard_name : null
}
output "cloudwatch_log_group_name" {
  description = "ECS backend CloudWatch log group name; null until hosting is enabled."
  value       = var.hosting_enabled ? module.hosting[0].cloudwatch_log_group_name : null
}
output "alb_zone_id" {
  description = "Canonical hosted zone ID of the EDIP ALB; null until hosting is enabled."
  value       = var.hosting_enabled ? module.hosting[0].alb_zone_id : null
}
output "acm_certificate_arn" {
  description = "ACM certificate ARN for the stable EDIP HTTPS endpoint; null until hosting is enabled."
  value       = var.hosting_enabled ? module.hosting[0].acm_certificate_arn : null
}
output "acm_dns_validation_records" {
  description = "DNS validation records to pass to the authoritative Vora DNS stack."
  value       = var.hosting_enabled ? module.hosting[0].acm_dns_validation_records : []
}
