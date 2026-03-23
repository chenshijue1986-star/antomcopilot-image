#!/bin/bash

# Quick view logs from Antom PSR Job Pod
# Usage: ./view-pod-logs.sh [job-name]

JOB_NAME=${1:-"antom-psr-test"}

echo "🔍 Finding pod for Job: $JOB_NAME"
echo "="

# Get pod name
POD_NAME=$(kubectl get pods -l job-name=$JOB_NAME -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)

if [ -z "$POD_NAME" ]; then
    echo "❌ No pods found for job: $JOB_NAME"
    echo ""
    echo "📋 Available jobs:"
    kubectl get jobs --no-headers -o custom-columns=NAME:.metadata.name 2>/dev/null || echo "No jobs found"
    exit 1
fi

echo "📦 Pod found: $POD_NAME"
echo ""
echo "📝 Streaming logs (Press Ctrl+C to stop):"
echo "="

# Stream logs in real-time
kubectl logs -f $POD_NAME
