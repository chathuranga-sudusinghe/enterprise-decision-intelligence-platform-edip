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
    actions = [
      "s3:GetAccelerateConfiguration",
      "s3:GetBucketAcl",
      "s3:GetBucketCORS",
      "s3:GetBucketLocation",
      "s3:GetBucketLogging",
      "s3:GetBucketObjectLockConfiguration",
      "s3:GetBucketOwnershipControls",
      "s3:GetBucketPolicy",
      "s3:GetBucketPublicAccessBlock",
      "s3:GetBucketRequestPayment",
      "s3:GetBucketTagging",
      "s3:GetBucketVersioning",
      "s3:GetBucketWebsite",
      "s3:GetEncryptionConfiguration",
      "s3:GetLifecycleConfiguration",
      "s3:GetReplicationConfiguration",
      "s3:ListBucket",
    ]
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
    actions = [
      "s3:CreateBucket",
      "s3:DeleteBucket",
      "s3:PutBucketOwnershipControls",
      "s3:PutBucketPolicy",
      "s3:PutBucketPublicAccessBlock",
      "s3:PutBucketTagging",
      "s3:PutBucketVersioning",
      "s3:PutEncryptionConfiguration",
      "s3:PutLifecycleConfiguration",
    ]
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

# Backend hosting additions are separate managed policies: existing foundation,
# state, ECR, S3 and release-role permissions above remain unchanged.
locals {
  hosting_name         = "${var.name_prefix}-${var.environment}"
  hosting_backend      = "${local.hosting_name}-backend"
  hosting_arn          = "arn:${data.aws_partition.current.partition}"
  hosting_account      = data.aws_caller_identity.current.account_id
  hosting_region       = "${var.aws_region}:${local.hosting_account}"
  hosting_ec2          = "${local.hosting_arn}:ec2:${local.hosting_region}"
  hosting_ecs          = "${local.hosting_arn}:ecs:${local.hosting_region}"
  hosting_elb          = "${local.hosting_arn}:elasticloadbalancing:${local.hosting_region}"
  hosting_cluster      = "${local.hosting_ecs}:cluster/${local.hosting_name}"
  hosting_service      = "${local.hosting_ecs}:service/${local.hosting_name}/backend"
  hosting_family       = "${local.hosting_ecs}:task-definition/${local.hosting_backend}:*"
  hosting_lb           = "${local.hosting_elb}:loadbalancer/app/${substr(local.hosting_backend, 0, 32)}/*"
  hosting_target       = "${local.hosting_elb}:targetgroup/${substr(local.hosting_backend, 0, 32)}/*"
  hosting_listener     = "${local.hosting_elb}:listener/app/${substr(local.hosting_backend, 0, 32)}/*"
  hosting_rule         = "${local.hosting_elb}:listener-rule/app/${substr(local.hosting_backend, 0, 32)}/*"
  hosting_logs         = "${local.hosting_arn}:logs:${local.hosting_region}:log-group:/ecs/${local.hosting_backend}"
  hosting_dashboard    = "${local.hosting_arn}:cloudwatch::${local.hosting_account}:dashboard/${local.hosting_backend}-operations"
  hosting_alarms       = [for suffix in ["unhealthy-target", "high-cpu", "high-memory"] : "${local.hosting_arn}:cloudwatch:${local.hosting_region}:alarm:${local.hosting_backend}-${suffix}"]
  hosting_roles        = [for suffix in ["execution", "task"] : "${local.hosting_arn}:iam::${local.hosting_account}:role/${local.hosting_backend}-${suffix}"]
  hosting_network_arns = [for kind in ["vpc", "subnet", "route-table", "internet-gateway", "security-group", "security-group-rule"] : "${local.hosting_ec2}:${kind}/*"]
  hosting_existing_tags = {
    "aws:ResourceTag/Project"     = var.name_prefix
    "aws:ResourceTag/Environment" = var.environment
  }
  hosting_new_tags = {
    "aws:RequestTag/Project"     = var.name_prefix
    "aws:RequestTag/Environment" = var.environment
  }

  hosting_read_statements = [
    # These discovery/read APIs do not support resource-level authorization.
    # RequestedRegion still prevents their use outside the EDIP deployment region.
    {
      Sid    = "RegionalDiscoveryWithoutResourceAuthorization"
      Effect = "Allow"
      Action = [
        "ec2:DescribeAvailabilityZones", "ec2:DescribeVpcs", "ec2:DescribeSubnets",
        "ec2:DescribeRouteTables", "ec2:DescribeInternetGateways", "ec2:DescribeSecurityGroups",
        "ec2:DescribeSecurityGroupRules", "ec2:DescribeNetworkInterfaces",
        "elasticloadbalancing:DescribeLoadBalancers", "elasticloadbalancing:DescribeLoadBalancerAttributes",
        "elasticloadbalancing:DescribeTargetGroups", "elasticloadbalancing:DescribeTargetGroupAttributes",
        "elasticloadbalancing:DescribeListeners", "elasticloadbalancing:DescribeListenerAttributes",
        "elasticloadbalancing:DescribeRules", "elasticloadbalancing:DescribeTags",
        "ecs:DescribeTaskDefinition", "logs:DescribeLogGroups",
      ]
      Resource  = "*"
      Condition = { StringEquals = { "aws:RequestedRegion" = var.aws_region } }
    },
    {
      Sid       = "ReadEdipVpcAttributes"
      Effect    = "Allow"
      Action    = ["ec2:DescribeVpcAttribute"]
      Resource  = "${local.hosting_ec2}:vpc/*"
      Condition = { StringEquals = local.hosting_existing_tags }
    },
    {
      Sid      = "ReadBackendEcs"
      Effect   = "Allow"
      Action   = ["ecs:DescribeClusters", "ecs:DescribeServices", "ecs:ListTagsForResource"]
      Resource = [local.hosting_cluster, local.hosting_service, local.hosting_family]
    },
    {
      Sid      = "ReadBackendLogTags"
      Effect   = "Allow"
      Action   = ["logs:ListTagsForResource", "logs:ListTagsLogGroup"]
      Resource = [local.hosting_logs, "${local.hosting_logs}:*"]
    },
    {
      Sid      = "ReadBackendDashboard"
      Effect   = "Allow"
      Action   = ["cloudwatch:GetDashboard"]
      Resource = local.hosting_dashboard
    },
    {
      Sid      = "ReadBackendAlarms"
      Effect   = "Allow"
      Action   = ["cloudwatch:DescribeAlarms", "cloudwatch:ListTagsForResource"]
      Resource = local.hosting_alarms
    },
    {
      Sid      = "ReadBackendRoles"
      Effect   = "Allow"
      Action   = ["iam:GetRole", "iam:GetRolePolicy", "iam:ListRolePolicies", "iam:ListAttachedRolePolicies", "iam:ListRoleTags"]
      Resource = local.hosting_roles
    },
  ]
  hosting_network_statements = concat(
    [for action, kind in {
      CreateVpc                     = "vpc"
      CreateSubnet                  = "subnet"
      CreateRouteTable              = "route-table"
      CreateInternetGateway         = "internet-gateway"
      CreateSecurityGroup           = "security-group"
      AuthorizeSecurityGroupIngress = "security-group-rule"
      AuthorizeSecurityGroupEgress  = "security-group-rule"
      } : {
      Sid       = "Tagged${action}"
      Effect    = "Allow"
      Action    = ["ec2:${action}"]
      Resource  = "${local.hosting_ec2}:${kind}/*"
      Condition = { StringEquals = local.hosting_new_tags }
    }],
    [
      {
        Sid       = "CreateChildrenOnlyInsideEdipVpc"
        Effect    = "Allow"
        Action    = ["ec2:CreateSubnet", "ec2:CreateRouteTable", "ec2:CreateSecurityGroup"]
        Resource  = "${local.hosting_ec2}:vpc/*"
        Condition = { StringEquals = local.hosting_existing_tags }
      },
      {
        Sid      = "TagOnlyNewEdipNetworkResources"
        Effect   = "Allow"
        Action   = ["ec2:CreateTags"]
        Resource = local.hosting_network_arns
        Condition = { StringEquals = merge(local.hosting_new_tags, {
          "ec2:CreateAction" = ["CreateVpc", "CreateSubnet", "CreateRouteTable", "CreateInternetGateway", "CreateSecurityGroup", "AuthorizeSecurityGroupIngress", "AuthorizeSecurityGroupEgress"]
        }) }
      },
      {
        Sid    = "ManageOnlyTaggedEdipNetwork"
        Effect = "Allow"
        Action = [
          "ec2:ModifyVpcAttribute", "ec2:DeleteVpc", "ec2:DeleteSubnet", "ec2:DeleteInternetGateway",
          "ec2:AttachInternetGateway", "ec2:DetachInternetGateway", "ec2:DeleteRouteTable",
          "ec2:CreateRoute", "ec2:ReplaceRoute", "ec2:DeleteRoute", "ec2:AssociateRouteTable",
          "ec2:DisassociateRouteTable", "ec2:ReplaceRouteTableAssociation", "ec2:DeleteSecurityGroup",
          "ec2:AuthorizeSecurityGroupIngress", "ec2:AuthorizeSecurityGroupEgress",
          "ec2:RevokeSecurityGroupIngress", "ec2:RevokeSecurityGroupEgress",
          "ec2:ModifySecurityGroupRules",
        ]
        Resource  = local.hosting_network_arns
        Condition = { StringEquals = local.hosting_existing_tags }
      },
      {
        Sid      = "MaintainTagsWithoutChangingOwnership"
        Effect   = "Allow"
        Action   = ["ec2:CreateTags", "ec2:DeleteTags"]
        Resource = local.hosting_network_arns
        Condition = {
          StringEquals                   = local.hosting_existing_tags
          "ForAllValues:StringNotEquals" = { "aws:TagKeys" = ["Project", "Environment"] }
        }
      },
    ]
  )
  hosting_runtime_statements = [
    {
      Sid    = "BackendLoadBalancerLifecycle"
      Effect = "Allow"
      Action = [
        "elasticloadbalancing:CreateLoadBalancer", "elasticloadbalancing:DeleteLoadBalancer",
        "elasticloadbalancing:ModifyLoadBalancerAttributes", "elasticloadbalancing:SetSecurityGroups",
        "elasticloadbalancing:SetSubnets", "elasticloadbalancing:CreateTargetGroup",
        "elasticloadbalancing:DeleteTargetGroup", "elasticloadbalancing:ModifyTargetGroup",
        "elasticloadbalancing:ModifyTargetGroupAttributes", "elasticloadbalancing:CreateListener",
        "elasticloadbalancing:DeleteListener", "elasticloadbalancing:ModifyListener",
        "elasticloadbalancing:CreateRule", "elasticloadbalancing:DeleteRule", "elasticloadbalancing:ModifyRule",
        "elasticloadbalancing:SetRulePriorities", "elasticloadbalancing:AddTags", "elasticloadbalancing:RemoveTags",
      ]
      Resource = [local.hosting_lb, local.hosting_target, local.hosting_listener, local.hosting_rule]
    },
    {
      Sid      = "BackendClusterAndServiceLifecycle"
      Effect   = "Allow"
      Action   = ["ecs:CreateCluster", "ecs:DeleteCluster", "ecs:CreateService", "ecs:DeleteService", "ecs:UpdateService", "ecs:TagResource", "ecs:UntagResource"]
      Resource = [local.hosting_cluster, local.hosting_service]
    },
    {
      Sid       = "RegisterOnlyBackendRevisions"
      Effect    = "Allow"
      Action    = ["ecs:RegisterTaskDefinition", "ecs:TagResource"]
      Resource  = local.hosting_family
      Condition = { StringEquals = local.hosting_new_tags }
    },
    {
      Sid      = "MaintainBackendRevisionTags"
      Effect   = "Allow"
      Action   = ["ecs:TagResource", "ecs:UntagResource"]
      Resource = local.hosting_family
    },
    {
      Sid      = "BackendLogGroupLifecycle"
      Effect   = "Allow"
      Action   = ["logs:CreateLogGroup", "logs:DeleteLogGroup", "logs:PutRetentionPolicy", "logs:DeleteRetentionPolicy", "logs:TagResource", "logs:UntagResource", "logs:TagLogGroup", "logs:UntagLogGroup"]
      Resource = [local.hosting_logs, "${local.hosting_logs}:*"]
    },
    {
      Sid      = "BackendDashboardLifecycle"
      Effect   = "Allow"
      Action   = ["cloudwatch:PutDashboard", "cloudwatch:DeleteDashboards"]
      Resource = local.hosting_dashboard
    },
    {
      Sid      = "BackendAlarmLifecycle"
      Effect   = "Allow"
      Action   = ["cloudwatch:PutMetricAlarm", "cloudwatch:DeleteAlarms", "cloudwatch:TagResource", "cloudwatch:UntagResource"]
      Resource = local.hosting_alarms
    },
    {
      Sid      = "ManageOnlyBackendRoles"
      Effect   = "Allow"
      Action   = ["iam:CreateRole", "iam:DeleteRole", "iam:PutRolePolicy", "iam:DeleteRolePolicy", "iam:TagRole", "iam:UntagRole", "iam:UpdateAssumeRolePolicy", "iam:UpdateRole", "iam:ListInstanceProfilesForRole"]
      Resource = local.hosting_roles
    },
    {
      Sid       = "PassOnlyBackendRolesToEcsTasks"
      Effect    = "Allow"
      Action    = ["iam:PassRole"]
      Resource  = local.hosting_roles
      Condition = { StringEquals = { "iam:PassedToService" = "ecs-tasks.amazonaws.com" } }
    },
  ]
}
resource "aws_iam_policy" "hosting" {
  for_each = {
    read    = jsonencode({ Version = "2012-10-17", Statement = local.hosting_read_statements })
    network = jsonencode({ Version = "2012-10-17", Statement = local.hosting_network_statements })
    runtime = jsonencode({ Version = "2012-10-17", Statement = local.hosting_runtime_statements })
  }
  name   = "${local.hosting_name}-hosting-${each.key}"
  policy = each.value
  lifecycle {
    precondition {
      condition     = length(each.value) <= 6144
      error_message = "Hosting managed policy exceeds AWS's 6144-character quota."
    }
  }
}
resource "aws_iam_role_policy_attachment" "hosting_plan" {
  role       = aws_iam_role.terraform_plan.name
  policy_arn = aws_iam_policy.hosting["read"].arn
}
resource "aws_iam_role_policy_attachment" "hosting_apply" {
  for_each   = aws_iam_policy.hosting
  role       = aws_iam_role.terraform_apply.name
  policy_arn = each.value.arn
}
