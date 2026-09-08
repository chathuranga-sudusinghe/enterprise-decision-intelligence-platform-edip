data "aws_iam_policy_document" "state_read_lock" {
  statement {
    actions   = ["s3:ListBucket"]
    resources = [local.state_bucket_arn]
    condition {
      test     = "StringEquals"
      variable = "s3:prefix"
      values   = [var.foundation_state_key, "${var.foundation_state_key}.tflock"]
    }

  }
  statement {
    actions   = ["s3:GetObject"]
    resources = [local.state_object_arn]
  }
  statement {
    actions   = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"]
    resources = [local.lock_object_arn]
  }
}
data "aws_iam_policy_document" "foundation_read" {
  statement {
    actions   = ["ecr:DescribeRepositories", "ecr:GetLifecyclePolicy", "ecr:ListTagsForResource"]
    resources = local.ecr_repository_arns
  }
  statement {
    actions   = ["s3:GetBucketLifecycleConfiguration", "s3:GetBucketLocation", "s3:GetBucketOwnershipControls", "s3:GetBucketPolicy", "s3:GetBucketPublicAccessBlock", "s3:GetBucketTagging", "s3:GetBucketVersioning", "s3:GetEncryptionConfiguration", "s3:ListBucket"]
    resources = [local.artifact_bucket_arn]
  }
  statement {
    actions   = ["iam:GetRole", "iam:GetRolePolicy", "iam:ListAttachedRolePolicies", "iam:ListRolePolicies", "iam:ListRoleTags"]
    resources = [local.release_role_arn]
  }
}
data "aws_iam_policy_document" "plan" {
  source_policy_documents = [data.aws_iam_policy_document.state_read_lock.json, data.aws_iam_policy_document.foundation_read.json]
}
resource "aws_iam_role_policy" "plan" {
  name   = "${local.plan_role_name}-policy"
  role   = aws_iam_role.terraform_plan.id
  policy = data.aws_iam_policy_document.plan.json
}
data "aws_iam_policy_document" "apply" {
  source_policy_documents = [data.aws_iam_policy_document.state_read_lock.json, data.aws_iam_policy_document.foundation_read.json]
  statement {
    actions   = ["s3:PutObject"]
    resources = [local.state_object_arn]
  }
  statement {
    actions   = ["ecr:CreateRepository", "ecr:DeleteRepository", "ecr:PutImageScanningConfiguration", "ecr:PutImageTagMutability", "ecr:PutLifecyclePolicy", "ecr:DeleteLifecyclePolicy", "ecr:TagResource", "ecr:UntagResource"]
    resources = local.ecr_repository_arns
  }
  statement {
    actions   = ["s3:CreateBucket", "s3:DeleteBucket", "s3:DeleteBucketEncryption", "s3:DeleteBucketLifecycle", "s3:DeleteBucketOwnershipControls", "s3:DeleteBucketPolicy", "s3:DeleteBucketPublicAccessBlock", "s3:DeleteBucketTagging", "s3:PutBucketLifecycleConfiguration", "s3:PutBucketOwnershipControls", "s3:PutBucketPolicy", "s3:PutBucketPublicAccessBlock", "s3:PutBucketTagging", "s3:PutBucketVersioning", "s3:PutEncryptionConfiguration"]
    resources = [local.artifact_bucket_arn]
  }
  statement {
    actions   = ["iam:CreateRole", "iam:DeleteRole", "iam:DeleteRolePolicy", "iam:PutRolePolicy", "iam:TagRole", "iam:UntagRole", "iam:UpdateAssumeRolePolicy", "iam:UpdateRole", "iam:ListInstanceProfilesForRole"]
    resources = [local.release_role_arn]
  }
}
resource "aws_iam_role_policy" "apply" {
  name   = "${local.apply_role_name}-policy"
  role   = aws_iam_role.terraform_apply.id
  policy = data.aws_iam_policy_document.apply.json
}
