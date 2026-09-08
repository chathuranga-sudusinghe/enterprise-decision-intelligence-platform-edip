data "aws_iam_policy_document" "github_actions_release_assume_role" {
  statement {
    sid     = "GitHubActionsOidc"
    effect  = "Allow"
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [var.github_oidc_provider_arn]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:sub"
      values   = sort(tolist(var.github_actions_release_oidc_subjects))
    }
  }
}

resource "aws_iam_role" "github_actions_release" {
  name                 = local.github_actions_release_role_name
  description          = "GitHub Actions release access to EDIP images and approved artifacts"
  assume_role_policy   = data.aws_iam_policy_document.github_actions_release_assume_role.json
  max_session_duration = 3600
}

data "aws_iam_policy_document" "github_actions_release" {
  statement {
    sid       = "AuthenticateToEcr"
    effect    = "Allow"
    actions   = ["ecr:GetAuthorizationToken"]
    resources = ["*"]
  }

  statement {
    sid    = "PublishAndReadApplicationImages"
    effect = "Allow"
    actions = [
      "ecr:BatchCheckLayerAvailability",
      "ecr:BatchGetImage",
      "ecr:CompleteLayerUpload",
      "ecr:DescribeImages",
      "ecr:DescribeRepositories",
      "ecr:GetDownloadUrlForLayer",
      "ecr:InitiateLayerUpload",
      "ecr:ListImages",
      "ecr:PutImage",
      "ecr:UploadLayerPart",
    ]
    resources = [for repository in aws_ecr_repository.application : repository.arn]
  }

  statement {
    sid       = "ReadArtifactBucketMetadata"
    effect    = "Allow"
    actions   = ["s3:GetBucketLocation", "s3:ListBucket"]
    resources = [aws_s3_bucket.artifacts.arn]
  }

  statement {
    sid    = "PublishAndReadApprovedArtifacts"
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:GetObjectTagging",
      "s3:GetObjectVersion",
      "s3:PutObject",
      "s3:PutObjectTagging",
    ]
    resources = ["${aws_s3_bucket.artifacts.arn}/*"]
  }
}

resource "aws_iam_role_policy" "github_actions_release" {
  name   = "${local.github_actions_release_role_name}-policy"
  role   = aws_iam_role.github_actions_release.id
  policy = data.aws_iam_policy_document.github_actions_release.json
}
