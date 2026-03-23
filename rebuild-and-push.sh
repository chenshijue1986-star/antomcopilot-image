#!/bin/bash

# Build and push Docker image for ACR

set -e

REPOSITORY="crpi-fm1vrihlw51dbs66.cn-hangzhou.personal.cr.aliyuncs.com/antomcopilot/antomcopilot-image"
TAG="latest"

echo "🚀 Building Docker image..."
echo "Repository: $REPOSITORY:$TAG"
echo ""

# Build
docker build -t $REPOSITORY:$TAG .

# Tag
docker tag $REPOSITORY:$TAG $REPOSITORY:$TAG

echo ""
echo "📤 Pushing to ACR..."
echo "Note: Make sure you have logged in to ACR:"
echo "  docker login --username=jephy1986 crpi-fm1vrihlw51dbs66.cn-hangzhou.personal.cr.aliyuncs.com"
echo ""

# Push
docker push $REPOSITORY:$TAG

echo ""
echo "✅ Image built and pushed successfully!"
echo "  $REPOSITORY:$TAG"