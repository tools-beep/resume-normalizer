#!/bin/bash
set -euo pipefail

# First-time setup for EC2 Ubuntu instance
# Run this ON the server after SSH-ing in:
#   curl -fsSL https://raw.githubusercontent.com/<user>/resume-normalizer/main/scripts/setup-server.sh | bash

echo "==> Installing Docker..."
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker "$USER"

echo "==> Docker installed. Log out and back in, then run:"
echo ""
echo "  git clone https://github.com/<your-user>/resume-normalizer.git"
echo "  cd resume-normalizer"
echo "  cp .env.prod.example .env.prod"
echo "  nano .env.prod  # fill in your values"
echo "  docker compose -f docker-compose.prod.yml up -d --build"
echo ""
echo "==> Done! Don't forget to point your domain's A record to this server's IP."
