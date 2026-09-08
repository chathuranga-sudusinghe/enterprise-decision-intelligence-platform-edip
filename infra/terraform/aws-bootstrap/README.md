# EDIP Terraform bootstrap

This root deliberately starts with local Terraform state because it creates the S3 bucket that will later hold its state. The tracked root has no active backend declaration. `backend.tf.example` is an inert template; the locally activated `backend.tf` and all state files are ignored by Git.

Keep `AWS_TERRAFORM_AUTOMATION_ENABLED` unset or different from the exact lowercase string `true` throughout bootstrap. Static PR validation continues while authenticated plans and applies remain skipped.


## Local bootstrap variables

`bootstrap.auto.tfvars` is intentionally ignored. Add the existing provider ARN to that local file alongside the other bootstrap inputs:

```hcl
github_oidc_provider_arn = "<existing-token.actions.githubusercontent.com-provider-arn>"
```

Obtain the value from the account owner or a read-only IAM lookup. Do not place an account-specific ARN in tracked files. EDIP owns only its scoped Terraform plan/apply roles and inline policies; the shared provider remains outside EDIP state. Do not import it unless a later account-level architecture decision explicitly transfers ownership to EDIP.

## Stage A: create the bootstrap foundation with local state

Supply the region, dedicated state bucket name, separate artifact bucket name, distinct bootstrap and foundation state keys, existing shared GitHub OIDC provider ARN, and exact plan/apply OIDC subjects outside version control. Use a separately governed short-lived operator identity, then run:

```bash
terraform init
terraform fmt -check -recursive
terraform validate
terraform plan -input=false -out=bootstrap.tfplan
terraform show -no-color bootstrap.tfplan
terraform apply -input=false bootstrap.tfplan
```

Review the saved plan before the final command. This is the only intentional local-state apply. Do not commit `terraform.tfstate`, its backup, the plan, credentials, variable values, or backend values. The bootstrap root creates the dedicated state bucket and separate Terraform plan/apply roles. It consumes the existing shared account-level GitHub OIDC provider and never creates, imports, changes, or destroys that provider. The state bucket is versioned, encrypted, private, TLS-only, and must differ from the application artifact bucket.

## Stage B: migrate bootstrap state to S3

After the Stage A apply succeeds, set `TF_STATE_BUCKET`, `TF_BOOTSTRAP_STATE_KEY`, and `TF_STATE_REGION` from reviewed bootstrap inputs/outputs. The bootstrap key defaults to `bootstrap/terraform.tfstate` and Terraform enforces that it differs from `foundation_state_key`. Activate the backend locally and migrate:

```bash
cp backend.tf.example backend.tf
terraform init -migrate-state \
  -backend-config="bucket=$TF_STATE_BUCKET" \
  -backend-config="key=$TF_BOOTSTRAP_STATE_KEY" \
  -backend-config="region=$TF_STATE_REGION" \
  -backend-config="encrypt=true" \
  -backend-config="use_lockfile=true"
terraform state list
aws s3api head-object \
  --bucket "$TF_STATE_BUCKET" \
  --key "$TF_BOOTSTRAP_STATE_KEY"
```

Confirm the remote object exists and Terraform can read the migrated state before removing local state copies. Preserve any required recovery copy only in encrypted, access-controlled storage outside the repository. Keep `backend.tf` local and protected; it is ignored because backend settings are environment-specific. S3 `.tflock` locking is used, with no DynamoDB table.

## Activate GitHub automation

Configure repository variables from the outputs: state bucket, externally managed shared OIDC provider ARN, plan role ARN, apply role ARN, foundation state key, region, artifact bucket, and release-role OIDC subjects. Configure `AWS_TERRAFORM_APPLY_ENVIRONMENT` with required reviewers and main-branch protection. Include exact pull-request and main-branch subjects in the plan role trust and an exact protected-environment subject in the apply role trust.

Only after migration and GitHub configuration are verified, set `AWS_TERRAFORM_AUTOMATION_ENABLED=true`. PRs then gain authenticated remote-state plans. Main changes create and upload an exact-commit binary and readable plan; protected-environment approval gates the dependent job that applies that saved plan.

The plan role can read main state and foundation resources and manage only its lockfile. The apply role can update main state and only the named ECR repositories, artifact bucket controls, and release role. Neither role can manage this bootstrap root or itself, and the application release role remains separate.
