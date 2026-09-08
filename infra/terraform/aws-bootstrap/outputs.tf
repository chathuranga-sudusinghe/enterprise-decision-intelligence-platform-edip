output "bootstrap_state_key" {
  description = "Bootstrap state key to use during post-bootstrap migration."
  value       = var.bootstrap_state_key
}
output "terraform_state_bucket_name" {
  value = aws_s3_bucket.terraform_state.bucket
}
output "github_oidc_provider_arn" {
  description = "Externally managed shared GitHub Actions OIDC provider ARN consumed by EDIP."
  value       = var.github_oidc_provider_arn
}
output "github_actions_terraform_plan_role_arn" {
  value = aws_iam_role.terraform_plan.arn
}
output "github_actions_terraform_apply_role_arn" {
  value = aws_iam_role.terraform_apply.arn
}
