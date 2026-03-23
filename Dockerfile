# Use AgentScope runtime sandbox browser image as base
FROM agentscope-registry.ap-southeast-1.cr.aliyuncs.com/agentscope/runtime-sandbox-browser:latest

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV TZ=Asia/Shanghai

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    libpq-dev \
    libfreetype6-dev \
    libpng-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Create working directory
WORKDIR /app

# Copy Python scripts
COPY query_antom_psr_data.py /app/
COPY analyse_and_gen_report.py /app/
COPY send_psr_report.py /app/

# Copy requirements and install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Create necessary directories
RUN mkdir -p /root/antom/success_rate

# Set Python path
ENV PYTHONPATH="/app:$PYTHONPATH"

# Make scripts executable
RUN chmod +x /app/*.py

# Create entrypoint script that supports both HTTP service mode and command mode
RUN echo '#!/bin/bash
# AgentScope PSR Analyzer Entrypoint
# Supports both HTTP service mode (AgentScope) and CLI mode

# If no arguments or first arg starts with "--", start HTTP service (AgentScope mode)
if [ $# -eq 0 ] || [[ "$1" == --* ]] || [[ "$1" == "serve" ]]; then
    # Start the original AgentScope sandbox HTTP service
    # The base image should have a default service, try to start it
    if [ -f /app/server.py ]; then
        echo "Starting AgentScope HTTP service..."
        exec python3 /app/server.py "$@"
    elif [ -f /app/main.py ]; then
        echo "Starting AgentScope HTTP service..."
        exec python3 /app/main.py "$@"
    elif [ -f /usr/local/bin/agentscope-sandbox ]; then
        echo "Starting AgentScope sandbox service..."
        exec /usr/local/bin/agentscope-sandbox "$@"
    else
        # Fallback: start a simple HTTP service for health checks
        echo "Starting fallback HTTP service on port 80..."
        exec python3 -c "
import http.server
import socketserver
import json

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == \"/healthz\":
            self.send_response(200)
            self.send_header(\"Content-type\", \"application/json\")
            self.end_headers()
            self.wfile.write(json.dumps({\"status\": \"healthy\"}).encode())
        else:
            self.send_response(200)
            self.send_header(\"Content-type\", \"text/plain\")
            self.end_headers()
            self.wfile.write(b\"AgentScope PSR Analyzer - OK\")
    
    def log_message(self, format, *args):
        pass

with socketserver.TCPServer((\"\", 80), Handler) as httpd:
    print(\"HTTP server listening on port 80\")
    httpd.serve_forever()
"
    fi
else
    # CLI mode: execute specific command
    CMD="$1"
    shift
    case "$CMD" in
        fetch)
            exec python3 /app/query_antom_psr_data.py "$@"
            ;;
        analyze)
            exec python3 /app/analyse_and_gen_report.py "$@"
            ;;
        send)
            exec python3 /app/send_psr_report.py "$@"
            ;;
        *)
            echo "Usage: docker run <image> {fetch|analyze|send} [args...]"
            echo "  fetch --date YYYYMMDD"
            echo "  analyze --date YYYYMMDD"
            echo "  send --date YYYYMMDD --recipient email@example.com"
            exit 1
            ;;
    esac
fi' > /entrypoint.sh && chmod +x /entrypoint.sh

# Set entrypoint
ENTRYPOINT ["/entrypoint.sh"]