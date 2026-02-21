## ADDED Requirements

### Requirement: Cloud Run service inaccessible from public internet
The master agent Cloud Run service SHALL be deployed with internal-only ingress, preventing direct access from the public internet.

#### Scenario: Internal ingress flag set in deploy script
- **WHEN** `deploy-agent.sh` is executed
- **THEN** the `gcloud run deploy` command includes `--ingress=internal`

#### Scenario: Internal ingress flag set in Cloud Build pipeline
- **WHEN** `cloudbuild.yaml` triggers a deployment
- **THEN** the `gcloud run deploy` step includes `--ingress=internal`

### Requirement: Cloud Run service requires IAM authentication
The master agent Cloud Run service SHALL require IAM authentication for all incoming requests (`--no-allow-unauthenticated`).

#### Scenario: Unauthenticated flag absent in deploy script
- **WHEN** `deploy-agent.sh` is executed
- **THEN** the `gcloud run deploy` command does NOT include `--allow-unauthenticated` and DOES include `--no-allow-unauthenticated`

#### Scenario: Unauthenticated flag absent in Cloud Build pipeline
- **WHEN** `cloudbuild.yaml` triggers a deployment
- **THEN** the `gcloud run deploy` step does NOT include `--allow-unauthenticated`

### Requirement: Direct VPC Egress configured in both deploy paths
The master agent SHALL use Direct VPC Egress (`--vpc-egress=all-traffic`) with a configurable VPC network and subnet in both deployment paths.

#### Scenario: VPC flags present in deploy script
- **WHEN** `deploy-agent.sh` is executed
- **THEN** the `gcloud run deploy` command includes `--network`, `--subnet`, and `--vpc-egress=all-traffic`

#### Scenario: VPC flags present in Cloud Build pipeline
- **WHEN** `cloudbuild.yaml` triggers a deployment
- **THEN** the `gcloud run deploy` step includes `--network`, `--subnet`, and `--vpc-egress=all-traffic` using substitution variables `_VPC_NETWORK` and `_VPC_SUBNET`

### Requirement: VPC configuration documented in environment template
The `VPC_NETWORK` and `VPC_SUBNET` environment variables SHALL be documented in `.env.example` so operators know which variables to set for VPC configuration.

#### Scenario: VPC variables present in .env.example
- **WHEN** an operator reads `.env.example`
- **THEN** they can find `VPC_NETWORK` and `VPC_SUBNET` with example values and explanatory comments
