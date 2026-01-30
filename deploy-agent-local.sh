#!/usr/bin/env bash
set -eo pipefail

SERVICE_NAME="${SERVICE_NAME:-ai-agent}"
IMAGE_NAME="${SERVICE_NAME}:local"
PORT="${PORT:-8080}"

echo "=== Building ${IMAGE_NAME} (native architecture) ==="
docker build -t "${IMAGE_NAME}" .

echo "=== Running ${IMAGE_NAME} on port ${PORT} ==="
DOCKER_ARGS="-d --rm --name ${SERVICE_NAME} -p ${PORT}:${PORT} -e PORT=${PORT}"

if [ -f .env ]; then
    DOCKER_ARGS="${DOCKER_ARGS} --env-file .env"
    echo "Using .env file"
fi

docker run ${DOCKER_ARGS} "${IMAGE_NAME}"

echo "=== ${SERVICE_NAME} running at http://localhost:${PORT} ==="
echo "Health check: curl http://localhost:${PORT}/health"
echo "Stop: docker stop ${SERVICE_NAME}"
