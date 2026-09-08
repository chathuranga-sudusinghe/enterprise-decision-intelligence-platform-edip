resource "aws_ecr_repository" "application" {
  for_each             = local.ecr_repository_names
  name                 = each.value
  image_tag_mutability = "IMMUTABLE"
  force_delete         = false
  encryption_configuration { encryption_type = "AES256" }
  image_scanning_configuration { scan_on_push = true }
}
resource "aws_ecr_lifecycle_policy" "application" {
  for_each   = aws_ecr_repository.application
  repository = each.value.name
  policy = jsonencode({ rules = [{
    rulePriority = 1
    description  = "Expire untagged images after the configured retention period"
    selection    = { tagStatus = "untagged", countType = "sinceImagePushed", countUnit = "days", countNumber = var.ecr_untagged_image_expiration_days }
    action       = { type = "expire" }
  }] })
}
