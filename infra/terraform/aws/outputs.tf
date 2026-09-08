output "backend_ecr_repository_url" {
  description = "Backend ECR repository URL."
  value       = aws_ecr_repository.application["backend"].repository_url
}
output "frontend_ecr_repository_url" {
  description = "Frontend ECR repository URL."
  value       = aws_ecr_repository.application["frontend"].repository_url
}
output "artifact_bucket_name" {
  description = "S3 bucket for approved model bundles and release artifacts."
  value       = aws_s3_bucket.artifacts.bucket
}
output "github_actions_release_role_arn" {
  description = "GitHub Actions OIDC release role ARN."
  value       = aws_iam_role.github_actions_release.arn
}
