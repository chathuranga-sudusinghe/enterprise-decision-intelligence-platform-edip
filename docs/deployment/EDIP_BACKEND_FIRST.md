# EDIP temporary backend deployment runbook

## Current implementation status

This is HTTP research/demo hosting, not public forecasting. See
[the ADR](../architecture/ADR_EDIP_MINIMUM_AWS_HOSTING.md).
The ALB forwards GET/HEAD for /health, /ready, /docs and /openapi.json;
everything else returns 403. Swagger needs /openapi.json. The schema contains
the forecast contract, but invoking it through the public ALB remains denied.
The task security group accepts 8000 only from the ALB.

Hosting defaults off. Terraform creates the service with zero tasks; CD starts
one task only after pushing a smoke-tested digest. No resources have been applied.

### Outstanding deployment prerequisites

1. Scoped bootstrap hosting permissions are implemented and planned but have not
   been applied. The plan/apply roles remain unchanged in AWS until the reviewed
   bootstrap plan is applied separately. Do not run the new CI path first.
2. The release trust configuration preserves the existing `main` subject and adds
   the exact protected-environment subject
   `repo:chathuranga-sudusinghe/enterprise-decision-intelligence-platform-edip:environment:production`.
   The live `production` environment deployment policy allows only `main`.
   Applying the bootstrap plan does not update this release trust; it changes when
   the separately reviewed foundation hosting plan is applied.
3. Docker Desktop WSL integration must be enabled for local build validation.
4. The artifact bucket was empty during inspection. Publish only the reviewed
   real model, capture BOTH object version IDs and hashes, and supply them below.
   The hosting preview used placeholder versions, was NOT saved, and is not
   deployable evidence.
5. Check that the account already has the ECS and ELB service-linked roles.
   Their absence requires an administrator to create the standard service-linked
   roles. This implementation does not modify shared account roles.
6. Review the ongoing cost of the ALB and public IPv4 addresses plus one
   0.5-vCPU/1-GiB task. One task is not highly available.

## Environment and model publication (operator actions, not yet executed)

Run at repository root using authorized short-lived AWS credentials. No access
keys belong in GitHub secrets or images. These commands are a runbook, not an
authorization to execute writes.

```bash
EDIP_REPO=$(gh repo view --json nameWithOwner --jq .nameWithOwner)
export AWS_REGION=$(gh variable get AWS_REGION --repo "$EDIP_REPO")
export TF_VAR_aws_region="$AWS_REGION"
export TF_VAR_artifact_bucket_name=$(gh variable get AWS_ARTIFACT_BUCKET_NAME --repo "$EDIP_REPO")
export TF_VAR_github_oidc_provider_arn=$(gh variable get AWS_GITHUB_OIDC_PROVIDER_ARN --repo "$EDIP_REPO")
export TF_VAR_github_actions_release_oidc_subjects=$(gh variable get AWS_RELEASE_OIDC_SUBJECTS_JSON --repo "$EDIP_REPO")
EDIP_ENVIRONMENT=$(gh variable get AWS_TERRAFORM_APPLY_ENVIRONMENT --repo "$EDIP_REPO")
# Preview the exact added subject locally; no remote configuration is changed here.
export TF_VAR_github_actions_release_oidc_subjects=$(jq -cn \
  --argjson existing "$TF_VAR_github_actions_release_oidc_subjects" \
  --arg subject "repo:$EDIP_REPO:environment:$EDIP_ENVIRONMENT" \
  '$existing + [$subject] | unique')

# Candidate identified in this workspace; review/approve it before publication.
EDIP_MODEL_DIR=artifacts/models/favorita_time_aware_origin_20170730_20260907T064049Z
EDIP_MODEL_PREFIX="models/$(basename "$EDIP_MODEL_DIR")"
EDIP_MODEL_VERSION=$(aws s3api put-object \
  --bucket "$TF_VAR_artifact_bucket_name" --key "$EDIP_MODEL_PREFIX/model.txt" \
  --body "$EDIP_MODEL_DIR/model.txt" --if-none-match '*' --query VersionId --output text)
EDIP_METADATA_VERSION=$(aws s3api put-object \
  --bucket "$TF_VAR_artifact_bucket_name" --key "$EDIP_MODEL_PREFIX/metadata.json" \
  --body "$EDIP_MODEL_DIR/metadata.json" --if-none-match '*' --query VersionId --output text)
EDIP_MODEL_HASH=$(sha256sum "$EDIP_MODEL_DIR/model.txt" | cut -d ' ' -f1)
EDIP_METADATA_HASH=$(sha256sum "$EDIP_MODEL_DIR/metadata.json" | cut -d ' ' -f1)
export TF_VAR_model_bundle=$(jq -cn \
  --arg prefix "$EDIP_MODEL_PREFIX" \
  --arg model_version_id "$EDIP_MODEL_VERSION" \
  --arg metadata_version_id "$EDIP_METADATA_VERSION" \
  --arg model_sha256 "$EDIP_MODEL_HASH" \
  --arg metadata_sha256 "$EDIP_METADATA_HASH" \
  '$ARGS.named')
export TF_VAR_hosting_enabled=true
```

The publication commands deliberately refuse overwriting existing keys. If keys
already exist, verify the existing object versions/hashes or choose a new reviewed
prefix. Do not upload the small local-api-test bundles as the research model.

## Review and apply the hosting plan

Only after the reviewed bootstrap IAM plan is applied:

```bash
terraform -chdir=infra/terraform/aws init -input=false \
  -backend-config="bucket=$(gh variable get AWS_TERRAFORM_STATE_BUCKET --repo "$EDIP_REPO")" \
  -backend-config="key=$(gh variable get AWS_TERRAFORM_STATE_KEY --repo "$EDIP_REPO")" \
  -backend-config="region=$AWS_REGION" \
  -backend-config=encrypt=true -backend-config=use_lockfile=true
terraform -chdir=infra/terraform/aws plan -input=false -out=hosting.tfplan
terraform -chdir=infra/terraform/aws show -no-color hosting.tfplan
# Execute only following a separate review/authorization:
terraform -chdir=infra/terraform/aws apply hosting.tfplan
terraform -chdir=infra/terraform/aws output -raw public_application_url
```

This creates zero running tasks, so an ALB URL alone does not mean a healthy app.
With the real selector and environment trust, the plan also changes release-role
trust. Do not replace its subject set with a single subject.

## GitHub release configuration and deployment

After approval, configure these repository variables consistently with the reviewed
Terraform inputs (these commands write GitHub configuration):

```bash
gh variable set AWS_MODEL_BUNDLE_JSON --repo "$EDIP_REPO" --body "$TF_VAR_model_bundle"
gh variable set AWS_RELEASE_OIDC_SUBJECTS_JSON --repo "$EDIP_REPO" --body "$TF_VAR_github_actions_release_oidc_subjects"
gh variable set AWS_HOSTING_ENABLED --repo "$EDIP_REPO" --body true
```

Retain AWS_TERRAFORM_AUTOMATION_ENABLED=true and the existing protected environment.
Publish source only through the user's separately approved Git/PR process.
A matching main push triggers Terraform plan -> protected saved-plan apply ->
protected image build/model smoke test/ECR push/ECS deployment -> Release Gate.
Do not enable hosting with missing model inputs or missing bootstrap permissions.

For a separately authorized manual first image release after infrastructure apply:

```bash
export DEPLOYMENT=$(terraform -chdir=infra/terraform/aws output -json application_hosting)
EDIP_ECR=$(jq -r .repository_url <<< "$DEPLOYMENT")
EDIP_IMAGE_TAG="$(git rev-parse HEAD)-$(date -u +%Y%m%dT%H%M%SZ)"
docker build --platform linux/amd64 -t "$EDIP_ECR:$EDIP_IMAGE_TAG" .
# Smoke-test this image and the reviewed bundle before pushing (workflow contains
# the complete test). Do not skip it because the Terraform plan is valid.
aws ecr get-login-password | docker login --username AWS --password-stdin "${EDIP_ECR%%/*}"
docker push "$EDIP_ECR:$EDIP_IMAGE_TAG"
EDIP_DIGEST=$(aws ecr describe-images --repository-name "${EDIP_ECR#*/}" \
  --image-ids "imageTag=$EDIP_IMAGE_TAG" --query 'imageDetails[0].imageDigest' --output text)
export IMAGE_DIGEST_URI="$EDIP_ECR@$EDIP_DIGEST"
python3 .github/scripts/deploy_backend.py
EDIP_URL=$(terraform -chdir=infra/terraform/aws output -raw public_application_url)
curl --fail "$EDIP_URL/ready"
# Open $EDIP_URL/docs in a browser.
# Forecast and metrics must return 403; never bypass the ALB with task ingress.
```

The automated workflow smoke-tests the approved real bundle before publishing,
checks the intended ECS revision (not only service stability), verifies allowed
and denied routes, and fails the release gate if any required stage fails.
CloudWatch logs are in /ecs/<prefix>-<environment>-backend and expire in seven days.
Terraform ignores service desired_count and task_definition; every release uses
the current Terraform template so configuration updates are not lost.
