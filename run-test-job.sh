#!/bin/bash

# Script to run Antom Payment Success Rate analyzer as Kubernetes Job
# Usage: ./run-test-job.sh [date] [recipient]

DATE=${1:-$(date +%Y%m%d)}
RECIPIENT=${2:-"test@example.com"}

echo "🚀 Creating Kubernetes Job to run Antom PSR analysis..."
echo "📅 Date: $DATE"
echo "📧 Recipient: $RECIPIENT"
echo ""

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
echo "✅ Job created successfully!"
echo ""
echo "📋 To check job status:"
echo "   kubectl get jobs"
echo ""
echo "📄 To view logs:"
echo "   kubectl logs -f job/antom-psr-test-${DATE}"
echo ""
echo "🗑️ To clean up:"
echo "   kubectl delete job antom-psr-test-${DATE}"
