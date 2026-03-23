#!/bin/bash

# Script to run Antom Payment Success Rate analyzer as Kubernetes Job
# Support full workflow with all parameters
# Usage:
#   Full workflow (fetch + analyze + send): ./run-test-job-v2.sh <date> <recipient>
#   Only send: ./run-test-job-v2.sh send <date> <recipient>
#   Only analyze: ./run-test-job-v2.sh analyze <date>
#   Only fetch: ./run-test-job-v2.sh fetch <date_range> [merchant_id] [merchant_token]

# Default values
DATE=$(date +%Y%m%d)
COMMAND="send"
RAW_ARGS=()

# Parse command line arguments
case "$1" in
    fetch|analyze|send)
        COMMAND="$1"
        shift
        ;;
    *)
        # If first argument looks like a date (8 digits), assume full workflow for send command
        if [[ "$1" =~ ^[0-9]{8}$ ]]; then
            DATE="$1"
            shift
        fi
        ;;
esac

# Set arguments based on command
case "$COMMAND" in
    fetch)
        DATE_RANGE="${1:-"$DATE~$DATE"}"
        MERCHANT_ID="${2:-""}"
        MERCHANT_TOKEN="${3:-""}"
        
        RAW_ARGS=("$COMMAND" "--date_range" "$DATE_RANGE")
        [ -n "$MERCHANT_ID" ] && RAW_ARGS+=("--merchant_id" "$MERCHANT_ID")
        [ -n "$MERCHANT_TOKEN" ] && RAW_ARGS+=("--merchant_token" "$MERCHANT_TOKEN")
        ;;
    analyze)
        ANALYZE_DATE="${1:-$DATE}"
        RAW_ARGS=("$COMMAND" "--date" "$ANALYZE_DATE")
        ;;
    send)
        SEND_DATE="${1:-$DATE}"
        RECIPIENT="${2:-"test@example.com"}"
        RAW_ARGS=("$COMMAND" "--date" "$SEND_DATE" "--recipient" "$RECIPIENT")
        ;;
    *)
        # Default: full workflow - send command
        SEND_DATE="${1:-$DATE}"
        RECIPIENT="${2:-"test@example.com"}"
        RAW_ARGS=("$COMMAND" "--date" "$SEND_DATE" "--recipient" "$RECIPIENT")
        ;;
esac

JOB_NAME="antom-psr-${COMMAND}-${DATE}"

echo "🚀 Creating Kubernetes Job to run Antom PSR analysis..."
echo "📝 Job Name: $JOB_NAME"
echo "🔧 Command: $COMMAND"
echo "📅 Date: $DATE"
[ "$COMMAND" == "send" ] && echo "📧 Recipient: ${RECIPIENT:-"(from config)"}"
[ "$COMMAND" == "fetch" ] && echo "📊 Date Range: ${DATE_RANGE:-$DATE~$DATE}"
[ -n "$MERCHANT_ID" ] && echo "🏪 Merchant ID: $MERCHANT_ID"
[ -n "$MERCHANT_TOKEN" ] && echo "🔑 Merchant Token: ${MERCHANT_TOKEN:0:10}..."
echo ""

# Delete existing job if it exists
echo "🔍 Checking if job already exists..."
if kubectl get job $JOB_NAME >/dev/null 2>&1; then
    echo "⚠️  Job $JOB_NAME already exists. Deleting it..."
    kubectl delete job $JOB_NAME
    echo "✅ Job deleted successfully"
    echo "⏳ Waiting 5 seconds for cleanup..."
    sleep 5
fi

echo ""
echo "📦 Creating new job..."

# Build YAML command and args
if [ ${#RAW_ARGS[@]} -eq 0 ]; then
    echo "❌ No arguments provided"
    exit 1
fi

# First argument is the command (fetch|analyze|send)
CMD_ARG="${RAW_ARGS[0]}"

# Remaining arguments are the args
ARGS_LIST=""
if [ ${#RAW_ARGS[@]} -gt 1 ]; then
    for arg in "${RAW_ARGS[@]:1}"; do
        ARGS_LIST="${ARGS_LIST}\n        - \"${arg}\""
    done
fi

# Create job manifest
cat <<EOF | kubectl apply -f -
apiVersion: batch/v1
kind: Job
metadata:
  name: $JOB_NAME
  namespace: default
spec:
  template:
    spec:
      imagePullSecrets:
      - name: acr-secret
      containers:
      - name: psr-analyzer
        image: crpi-fm1vrihlw51dbs66.cn-hangzhou.personal.cr.aliyuncs.com/antomcopilot/antomcopilot-image:latest
        command: ["$CMD_ARG"]
        args:${ARGS_LIST:- []}
        env:
        - name: PYTHONPATH
          value: "/app"
        volumeMounts:
        - name: antom-config
          mountPath: /root/antom
          readOnly: true
      volumes:
      - name: antom-config
        hostPath:
          path: /Users/chenshijue/antom
          type: Directory
      restartPolicy: Never
  backoffLimit: 2
