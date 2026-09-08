# EDIP Terraform bootstrap

This root must be applied once with a separately governed short-lived operator identity before the main `infra/terraform/aws` root can use remote state or GitHub OIDC.

## Bootstrap order

1. Leave `AWS_TERRAFORM_AUTOMATION_ENABLED` unset or set to any value other than the exact lowercase string `true`. PR static validation continues, while authenticated plans and applies remain skipped.
2. Supply the region, dedicated state bucket name, separate artifact bucket name, main state key, exact plan subjects, and exact protected-environment apply subjects outside version control.
3. Run `terraform init -backend=false`, review a local bootstrap plan, and apply this root with short-lived bootstrap credentials. This is the only unavoidable local-state phase; never commit that state.
4. Reinitialize this bootstrap root with its own key in the new bucket and `use_lockfile=true`, migrating the bootstrap state when Terraform prompts.
5. Configure GitHub repository variables from the outputs: state bucket, shared OIDC provider ARN, plan role ARN, apply role ARN, state key, region, artifact bucket, and release-role OIDC subjects.
6. Configure `AWS_TERRAFORM_APPLY_ENVIRONMENT` as a protected GitHub environment with required reviewers and main-branch deployment protection.
7. Set `AWS_TERRAFORM_AUTOMATION_ENABLED` to the exact lowercase string `true` only after the bootstrap outputs, repository variables, and protected environment are ready.
8. PRs to `dev` or `main` can then use the read-only plan role. A merge to `main` invokes a post-merge plan job with that same role; include the exact main-branch OIDC subject in the plan role trust.
9. Review the uploaded `tfplan.txt` artifact. Approving the protected apply environment then permits the dependent job to apply the matching binary `tfplan` artifact from that workflow run.

The plan role can read the main state and approved foundation resources and can create/delete only the S3 lockfile. The apply role can update the main state and manage only the named ECR repositories, application artifact bucket controls, and application release role. Neither role can manage this bootstrap root, its own policy/trust, or unrelated resources. The release role remains separate.

The state bucket is versioned, encrypted, private, TLS-only, and must differ from the application artifact bucket. Locking uses `<state-key>.tflock`; no DynamoDB table is used.

## Automation gate

Before activation, relevant PRs always run formatting, backend-disabled initialization, and validation for both AWS Terraform roots. The authenticated remote-state plan job is skipped. Main pushes may trigger the apply workflow, but its apply job is skipped before environment evaluation and AWS authentication.

After activation, PRs retain static checks and add authenticated remote-state plans. A main push affecting the AWS foundation creates a new plan from the exact triggering commit with the read-only plan role and uploads its binary and readable forms for three days. Only after that succeeds does the protected-environment apply job request approval. The apply job checks out the same commit and applies the downloaded binary plan without creating another plan. Changing the gate does not replace protected-environment approval.
