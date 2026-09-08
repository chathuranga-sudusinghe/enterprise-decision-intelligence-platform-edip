# EDIP AWS Terraform foundation

This root defines EDIP's first production AWS foundation: private image and artifact storage plus a GitHub Actions OpenID Connect (OIDC) trust boundary. It does not deploy workloads.

It manages immutable, scan-on-push backend and frontend Amazon Elastic Container Registry (ECR) repositories; a private, versioned, AES-256 encrypted Amazon Simple Storage Service (S3) artifact bucket with public access blocked, customer-provided encryption keys blocked, Transport Layer Security enforced, and incomplete uploads cleaned up; and a narrowly scoped application release role. It consumes an externally managed shared GitHub OIDC provider ARN.

## Release role boundary

The `github_actions_release` role is reserved for future application release and continuous deployment workflows. It can authenticate to ECR, push and read images in the two EDIP repositories, list the EDIP artifact bucket, and publish or read approved artifact objects. It cannot change ECR repository configuration, S3 bucket configuration, its own IAM policy or trust policy, the OIDC provider, or any unrelated infrastructure. It has no resource creation or deletion permissions.

The separate `infra/terraform/aws-bootstrap` root consumes the external shared OIDC provider and creates narrowly scoped GitHub Actions Terraform plan and apply roles. Those roles own reviewed plan/apply permissions and state-backend access for this root. This release role must not be reused for Terraform applies.

Amazon Elastic Container Service (ECS), Fargate, Application Load Balancer, CloudWatch, Secrets Manager, databases, application deployment, and continuous deployment remain deferred.

## Inputs and authentication

Supply `aws_region`, globally unique `artifact_bucket_name`, and exact `github_actions_release_oidc_subjects` outside version control. Other names, retention values, and tags are configurable. Wildcard OIDC subjects are rejected; use approved protected branches, release tags, or GitHub environments. A branch subject has the shape `repo:OWNER/REPOSITORY:ref:refs/heads/BRANCH`.

Terraform uses the standard AWS provider credential chain. Operators must use short-lived AWS IAM Identity Center or equivalent credentials; workflows must use OIDC. Do not create long-lived AWS credential secrets.

## Remote-state bootstrap

This root cannot safely create its own state backend. A separately reviewed bootstrap must first create a dedicated S3 state bucket with versioning, encryption, public access blocked, and tightly scoped access. Keep it separate from this artifact bucket. Initialize with partial backend configuration:

```bash
terraform init \
  -backend-config="bucket=$TF_STATE_BUCKET" \
  -backend-config="key=$TF_STATE_KEY" \
  -backend-config="region=$TF_STATE_REGION" \
  -backend-config="encrypt=true" \
  -backend-config="use_lockfile=true"
```

Do not commit backend values. S3 lockfiles are required; DynamoDB locking is deprecated. The bootstrap root must be applied first with a separately governed short-lived identity; this root then consumes its OIDC provider ARN and remote backend. The separate `terraform-apply.yml` workflow remains disabled until `AWS_TERRAFORM_AUTOMATION_ENABLED` is exactly `true` and then requires the configured protected environment. When enabled, its read-only plan job uploads the exact post-merge binary and readable plan before the dependent protected-environment job requests approval and applies that saved plan.

## Local validation

```bash
terraform fmt -check -recursive
terraform init -backend=false -input=false
terraform validate
```

A real plan or apply requires the remote backend, required variables, and authorized short-lived credentials. Never use local state for production.
