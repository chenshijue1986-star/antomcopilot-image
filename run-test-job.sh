#!/bin/bash

# Script to run Antom Payment Success Rate analyzer as Kubernetes Job
# Usage: ./run-test-job.sh [date] [recipient]

DATE=${1:-$(date +%Y%m%d)}
RECIPIENT=${2:-"test@example.com"}
JOB_NAME="antom-psr-test-${DATE}"

echo "🚀 Creating Kubernetes Job to run Antom PSR analysis..."
echo "📅 Date: $DATE"
echo "📧 Recipient: $RECIPIENT"
echo "📝 Job Name: $JOB_NAME"
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

# Create job manifest
cat <<EOF | kubectl apply -f -
apiVersion: batch/v1
kind: Job
metadata:
  name: antom-psr-test-${DATE}
  namespace: default
spec:
  template:
    spec:
      containers:
      - name: psr-analyzer
        image: crpi-fm1vrihlw51dbs66.cn-hangzhou.personal.cr.aliyuncs.com/antomcopilot/antomcopilot-image:latest
        command: ["send"]
        args:
        - "--date"
        - "$DATE"
        - "--recipient"
        - "$RECIPIENT"
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
EOF

echo ""
if [ $? -eq 0 ]; then
    echo "✅ Job created successfully!"
else
    echo "❌ Failed to create job"
    exit 1
fi

echo ""
echo "📋 To check job status:"
echo "   kubectl get job $JOB_NAME"
echo ""
echo "📄 To view logs:"
echo "   kubectl logs -f job/$JOB_NAME"
echo ""
echo "🗑️ To clean up:"
echo "   kubectl delete job $JOB_NAME"
