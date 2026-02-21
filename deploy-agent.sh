#!/usr/bin/env bash
set -euo pipefail

# --- Configuration ---
PROJECT_ID="${PROJECT_ID:-gen-lang-client-0741140892}"
SERVICE_NAME="${SERVICE_NAME:-master-agent}"
REGION="${REGION:-europe-west4}"
DOCKER_REGISTRY="${DOCKER_REGISTRY:-gcr.io}"
LOG_LEVEL="${LOG_LEVEL:-INFO}"

# --- Timestamped log ---
LOG_FILE="deploy-agent-$(date +%Y%m%d-%H%M%S).log"
exec > >(tee -a "${LOG_FILE}") 2>&1
echo "=== Deploy log: ${LOG_FILE} ==="
echo "=== Started: $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="

# --- PORT guard ---
unset PORT
# shellcheck disable=SC2153
if echo "${ENV_VARS:-}" | grep -q "PORT="; then
    echo "ERROR: ENV_VARS must not contain PORT. Cloud Run injects PORT automatically."
    exit 1
fi

# --- --no-cache support ---
BUILD_EXTRA_ARGS=""
if [[ "${1:-}" == "--no-cache" ]]; then
    BUILD_EXTRA_ARGS="--no-cache"
    echo "Build: --no-cache enabled"
fi

# --- GIT_SHA ---
GIT_SHA="${GIT_SHA:-$(git rev-parse --short HEAD 2>/dev/null || echo '')}"

# --- Image base ---
if [[ "${DOCKER_REGISTRY}" == *"pkg.dev" ]]; then
    if [[ -z "${AR_REPO_NAME:-}" ]]; then
        echo "ERROR: AR_REPO_NAME is required when DOCKER_REGISTRY ends with pkg.dev"
        exit 1
    fi
    IMAGE_BASE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${AR_REPO_NAME}/${SERVICE_NAME}"
else
    IMAGE_BASE="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"
fi

IMAGE_LATEST="${IMAGE_BASE}:latest"
echo "Image: ${IMAGE_LATEST}"

# --- Build ---
echo "=== Building with Cloud Build ==="
gcloud builds submit \
    --project="${PROJECT_ID}" \
    --tag="${IMAGE_LATEST}" \
    ${BUILD_EXTRA_ARGS} \
    --quiet

# Tag with GIT_SHA if available
if [[ -n "${GIT_SHA}" ]]; then
    IMAGE_SHA="${IMAGE_BASE}:${GIT_SHA}"
    echo "Tagging: ${IMAGE_SHA}"
    gcloud container images add-tag "${IMAGE_LATEST}" "${IMAGE_SHA}" \
        --project="${PROJECT_ID}" \
        --quiet
fi

# --- Deploy ---
echo "=== Deploying to Cloud Run ==="
AGENT_PROMPT_ID="${AGENT_PROMPT_ID:-5914177388295487488}"
AGENT_ENGINE_ID="${AGENT_ENGINE_ID:-5316939164761980928}"

DOCLING_AGENT_URL="${DOCLING_AGENT_URL:-https://docling-agent-3qblthn7ba-ez.a.run.app}"
VPC_NETWORK="${VPC_NETWORK:-default}"
VPC_SUBNET="${VPC_SUBNET:-default}"
VPC_ROUTER="${VPC_ROUTER:-nat-router}"
VPC_NAT="${VPC_NAT:-nat-config}"

# --- Ensure Cloud NAT exists (required for vpc-egress=all-traffic + internet access) ---
echo "=== Ensuring Cloud NAT exists ==="
if ! gcloud compute routers describe "${VPC_ROUTER}" \
    --region="${REGION}" --project="${PROJECT_ID}" &>/dev/null; then
    echo "Creating Cloud Router: ${VPC_ROUTER}"
    gcloud compute routers create "${VPC_ROUTER}" \
        --region="${REGION}" \
        --network="${VPC_NETWORK}" \
        --project="${PROJECT_ID}"
else
    echo "Cloud Router ${VPC_ROUTER} already exists"
fi

if ! gcloud compute routers nats describe "${VPC_NAT}" \
    --router="${VPC_ROUTER}" \
    --region="${REGION}" --project="${PROJECT_ID}" &>/dev/null; then
    echo "Creating Cloud NAT: ${VPC_NAT}"
    gcloud compute routers nats create "${VPC_NAT}" \
        --router="${VPC_ROUTER}" \
        --region="${REGION}" \
        --auto-allocate-nat-external-ips \
        --nat-all-subnet-ip-ranges \
        --project="${PROJECT_ID}"
else
    echo "Cloud NAT ${VPC_NAT} already exists"
fi

ENV_VARS="GCP_PROJECT_ID=${PROJECT_ID}"
ENV_VARS="${ENV_VARS},GCP_LOCATION=${REGION}"
ENV_VARS="${ENV_VARS},GOOGLE_CLOUD_PROJECT=${PROJECT_ID}"
ENV_VARS="${ENV_VARS},GOOGLE_CLOUD_LOCATION=${REGION}"
ENV_VARS="${ENV_VARS},GOOGLE_GENAI_USE_VERTEXAI=true"
ENV_VARS="${ENV_VARS},AGENT_PROMPT_ID=${AGENT_PROMPT_ID}"
ENV_VARS="${ENV_VARS},AGENT_ENGINE_ID=${AGENT_ENGINE_ID}"
ENV_VARS="${ENV_VARS},LOG_LEVEL=${LOG_LEVEL}"
ENV_VARS="${ENV_VARS},DOCLING_AGENT_URL=${DOCLING_AGENT_URL}"
if [[ -n "${MODEL_NAME:-}" ]]; then
    ENV_VARS="${ENV_VARS},MODEL_NAME=${MODEL_NAME}"
fi
if [[ -n "${MODEL_ENDPOINT:-}" ]]; then
    ENV_VARS="${ENV_VARS},MODEL_ENDPOINT=${MODEL_ENDPOINT}"
fi

gcloud run deploy "${SERVICE_NAME}" \
    --project="${PROJECT_ID}" \
    --region="${REGION}" \
    --image="${IMAGE_LATEST}" \
    --platform=managed \
    --ingress=internal \
    --no-allow-unauthenticated \
    --network="${VPC_NETWORK}" \
    --subnet="${VPC_SUBNET}" \
    --vpc-egress=all-traffic \
    --set-env-vars="${ENV_VARS}" \
    --set-secrets="MODEL_API_KEY=GOOGLE_API_KEY:latest" \
    --quiet

echo "=== Deploy complete: $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
SERVICE_URL=$(gcloud run services describe "${SERVICE_NAME}" \
    --project="${PROJECT_ID}" \
    --region="${REGION}" \
    --format="value(status.url)" \
    --quiet)
echo "Service URL: ${SERVICE_URL}"
