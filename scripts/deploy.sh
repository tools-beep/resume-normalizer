#!/bin/bash
set -euo pipefail

# Deploy resume-normalizer to EC2 instance
# Usage: ./scripts/deploy.sh <EC2_HOST>
# Example: ./scripts/deploy.sh ubuntu@52.12.34.56

HOST="${1:?Usage: $0 <user@host>}"
APP_DIR="resume-normalizer"

echo "==> Deploying to $HOST..."

# Push latest code
ssh "$HOST" "cd $APP_DIR && git pull"

# Rebuild and restart
ssh "$HOST" "cd $APP_DIR && docker compose -f docker-compose.prod.yml up -d --build"

# Wait for health check
echo "==> Waiting for health check..."
sleep 5

ssh "$HOST" "curl -sf http://localhost:8000/api/v1/health" && \
  echo "==> Deploy successful!" || \
  echo "==> WARNING: Health check failed. Check logs with: docker compose -f docker-compose.prod.yml logs api"
