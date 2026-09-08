data "aws_iam_policy_document" "plan_assume" {
  statement {
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
      values   = sort(tolist(var.github_actions_plan_oidc_subjects))
    }

  }
}
data "aws_iam_policy_document" "apply_assume" {
  statement {
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
      values   = sort(tolist(var.github_actions_apply_oidc_subjects))
    }

  }
}
resource "aws_iam_role" "terraform_plan" {
  lifecycle {
    precondition {
      condition     = local.plan_role_name != local.apply_role_name && local.plan_role_name != local.release_role_name
      error_message = "Terraform plan, Terraform apply, and application release roles must have distinct names."
    }
  }
  name               = local.plan_role_name
  description        = "GitHub Actions read-only Terraform plan role"
  assume_role_policy = data.aws_iam_policy_document.plan_assume.json
}
resource "aws_iam_role" "terraform_apply" {
  lifecycle {
    precondition {
      condition     = local.apply_role_name != local.release_role_name
      error_message = "Terraform apply and application release roles must have distinct names."
    }
  }
  name               = local.apply_role_name
  description        = "GitHub Actions scoped apply role for the approved AWS foundation"
  assume_role_policy = data.aws_iam_policy_document.apply_assume.json
}
