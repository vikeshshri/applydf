#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${AWS_REGION:-}" || -z "${ECR_REGISTRY:-}" || -z "${BACKEND_IMAGE:-}" || -z "${FRONTEND_IMAGE:-}" ]]; then
  echo "Missing required environment variables."
  exit 1
fi

APP_DIR="/opt/applydf"
mkdir -p "$APP_DIR"
cd "$APP_DIR"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is not installed on EC2. Install Docker first."
  exit 1
fi

if ! docker compose version >/dev/null 2>&1; then
  echo "Docker Compose plugin not found. Install docker compose plugin first."
  exit 1
fi

if ! command -v aws >/dev/null 2>&1; then
  echo "AWS CLI is not installed on EC2. Install AWS CLI first."
  exit 1
fi

aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "$ECR_REGISTRY"

cat > .env.aws <<EOF
BACKEND_IMAGE=${BACKEND_IMAGE}
FRONTEND_IMAGE=${FRONTEND_IMAGE}
EOF

if [[ ! -f docker-compose.aws.yml ]]; then
  echo "docker-compose.aws.yml not found in ${APP_DIR}."
  echo "Copy deploy/docker-compose.aws.yml from the repository to ${APP_DIR}."
  exit 1
fi

docker compose --env-file .env.aws -f docker-compose.aws.yml pull
docker compose --env-file .env.aws -f docker-compose.aws.yml up -d --remove-orphans
docker image prune -af --filter "until=72h"

echo "Deployment complete."
