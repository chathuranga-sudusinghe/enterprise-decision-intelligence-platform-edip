output "terraform_state_bucket_name" {
  value = aws_s3_bucket.terraform_state.bucket
}
output "github_oidc_provider_arn" {
  value = aws_iam_openid_connect_provider.github.arn
}
output "github_actions_terraform_plan_role_arn" {
  value = aws_iam_role.terraform_plan.arn
}
output "github_actions_terraform_apply_role_arn" {
  value = aws_iam_role.terraform_apply.arn
}
