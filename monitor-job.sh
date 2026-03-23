#!/bin/bash

# Monitor Antom PSR Job execution
# Usage: ./monitor-job.sh [job-name]

JOB_NAME=${1:-"antom-psr-test-20260323"}

echo "🔍 Monitoring Job: $JOB_NAME"
echo "="
echo ""

# Function to get pod name
get_pod_name() {
    kubectl get pods -l job-name=$JOB_NAME -o jsonpath='{.items[0].metadata.name}' 2>/dev/null
}

# Monitor loop
counter=0
while true; do
    ((counter++))
    
    clear
    echo "🔍 Monitoring Job: $JOB_NAME (Update: $counter)"
    echo "="
    echo ""
    
    # Show Job status
    echo "📊 JOB STATUS:"
    kubectl get job $JOB_NAME -o wide 2>/dev/null || echo "Job not found"
    echo ""
    
    # Show Pod status
    echo "📦 POD STATUS:"
    kubectl get pods -l job-name=$JOB_NAME --show-labels 2>/dev/null || echo "No pods found"
    echo ""
    
    # Get pod name
    POD_NAME=$(get_pod_name)
    
    if [ ! -z "$POD_NAME" ]; then
        # Show Pod phase
        PHASE=$(kubectl get pod $POD_NAME -o jsonpath='{.status.phase}' 2>/dev/null)
        echo "🎮 POD PHASE: $PHASE"
        echo ""
        
        # Show container status
        echo "🔧 CONTAINER STATUS:"
        kubectl get pod $POD_NAME -o jsonpath='{.status.containerStatuses[0].state}' 2>/dev/null | jq -r . 2>/dev/null || \
        kubectl get pod $POD_NAME -o custom-columns=STATE:.status.containerStatuses[0].state --no-headers 2>/dev/null
        echo ""
        
        # Show recent events
        echo "📋 RECENT EVENTS:"
        kubectl get events --field-selector involvedObject.name=$POD_NAME --sort-by='.lastTimestamp' -o custom-columns=TIME:.lastTimestamp,TYPE:.type,REASON:.reason,MESSAGE:.message --no-headers 2>/dev/null | tail -5 || echo "No recent events"
        echo ""
        
        # Show last 10 lines of logs if pod is running or completed
        if [ "$PHASE" == "Running" ] || [ "$PHASE" == "Succeeded" ] || [ "$PHASE" == "Failed" ]; then
            echo "📝 LAST LOG LINES:"
            kubectl logs --tail=10 $POD_NAME 2>/dev/null || echo "No logs yet"
            echo ""
        fi
        
        # Check if job completed
        COMPLETIONS=$(kubectl get job $JOB_NAME -o jsonpath='{.status.succeeded}' 2>/dev/null)
        if [ "$COMPLETIONS" == "1" ]; then
            echo "✅ JOB COMPLETED SUCCESSFULLY!"
            echo ""
            echo "📝 FULL LOGS:"
            kubectl logs $POD_NAME
            break
        fi
        
        FAILED=$(kubectl get job $JOB_NAME -o jsonpath='{.status.failed}' 2>/dev/null)
        if [ "$FAILED" == "1" ]; then
            echo "❌ JOB FAILED!"
            echo ""
            echo "📝 ERROR LOGS:"
            kubectl logs $POD_NAME
            break
        fi
    fi
    
    echo "⏳ Job is still running... (Press Ctrl+C to exit)"
    sleep 5
done

echo ""
echo "🧹 Cleaning up..."
kubectl delete job $JOB_NAME 2>/dev/null
echo "✅ Done!"
