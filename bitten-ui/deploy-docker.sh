#!/bin/bash

# BITTEN UI - Docker Deployment Script
# Builds and runs containerized production deployment

set -e

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  🐳 BITTEN UI - Docker Production Deployment"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Configuration
IMAGE_NAME="bitten-ui"
CONTAINER_NAME="bitten-ui"
PORT=3000

# Stop and remove existing container
echo ""
echo "🛑 Stopping existing container..."
docker stop $CONTAINER_NAME 2>/dev/null || true
docker rm $CONTAINER_NAME 2>/dev/null || true

# Build image
echo ""
echo "📦 Building Docker image..."
docker build -t $IMAGE_NAME:latest -f Dockerfile .

if [ $? -ne 0 ]; then
    echo "❌ Docker build failed"
    exit 1
fi

echo "✅ Docker image built successfully"

# Run container
echo ""
echo "🚀 Starting container..."
docker run -d \
  --name $CONTAINER_NAME \
  -p $PORT:3000 \
  --env-file .env.production \
  --restart unless-stopped \
  $IMAGE_NAME:latest

if [ $? -ne 0 ]; then
    echo "❌ Container failed to start"
    exit 1
fi

# Wait for container to be healthy
echo ""
echo "⏳ Waiting for container to be ready..."
sleep 5

# Check if container is running
if docker ps | grep -q $CONTAINER_NAME; then
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  ✅ DEPLOYMENT SUCCESSFUL"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "🌐 App running at: http://localhost:$PORT"
    echo "🐳 Container: $CONTAINER_NAME"
    echo ""
    echo "📋 Useful commands:"
    echo "  View logs:    docker logs -f $CONTAINER_NAME"
    echo "  Stop:         docker stop $CONTAINER_NAME"
    echo "  Restart:      docker restart $CONTAINER_NAME"
    echo "  Remove:       docker rm -f $CONTAINER_NAME"
    echo ""
    echo "📋 Next steps:"
    echo "  1. Set up NGINX reverse proxy with SSL"
    echo "  2. Configure domain DNS"
    echo "  3. Run smoke tests"
    echo ""
else
    echo "❌ Container failed to start"
    docker logs $CONTAINER_NAME
    exit 1
fi
