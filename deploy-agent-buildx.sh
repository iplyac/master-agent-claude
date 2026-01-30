#!/usr/bin/env bash
set -euo pipefail

# --- Configuration ---
PROJECT_ID="${PROJECT_ID:-gen-lang-client-0741140892}"
SERVICE_NAME="${SERVICE_NAME:-ai-agent}"
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
if echo "${ENV_VARS:-}" | grep -q "PORT="; then
    echo "ERROR: ENV_VARS must not contain PORT. Cloud Run injects PORT automatically."
    exit 1
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

# --- Build with Buildx ---
echo "=== Building with Docker Buildx (linux/amd64) ==="
TAGS="--tag ${IMAGE_LATEST}"
if [[ -n "${GIT_SHA}" ]]; then
    TAGS="${TAGS} --tag ${IMAGE_BASE}:${GIT_SHA}"
fi

docker buildx build \
    --platform linux/amd64 \
    ${TAGS} \
    --push \
    .

# --- Deploy ---
echo "=== Deploying to Cloud Run ==="
ENV_VARS="PORT=8080,LOG_LEVEL=${LOG_LEVEL}"
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
    --allow-unauthenticated \
    --set-env-vars="${ENV_VARS}" \
    --set-secrets="MODEL_API_KEY=MODEL_API_KEY:latest" \
    --quiet

echo "=== Deploy complete: $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
SERVICE_URL=$(gcloud run services describe "${SERVICE_NAME}" \
    --project="${PROJECT_ID}" \
    --region="${REGION}" \
    --format="value(status.url)" \
    --quiet)
echo "Service URL: ${SERVICE_URL}"
