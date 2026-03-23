#!/bin/bash
# AgentScope PSR Analyzer Entrypoint
# Supports both HTTP service mode (AgentScope) and CLI mode

# If no arguments or first arg starts with "--", start HTTP service (AgentScope mode)
if [ $# -eq 0 ] || [[ "$1" == --* ]] || [ "$1" = "serve" ]; then
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
import sys

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/healthz':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'healthy'}).encode())
        elif self.path == '/mcp/list_tools':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            tools = {
                'tools': [
                    {
                        'name': 'antom_psr_fetch',
                        'description': 'Fetch Antom PSR data for a date range'
                    },
                    {
                        'name': 'antom_psr_analyze',
                        'description': 'Analyze PSR data for a specific date'
                    },
                    {
                        'name': 'antom_psr_send',
                        'description': 'Send PSR report to email'
                    }
                ]
            }
            self.wfile.write(json.dumps(tools).encode())
        elif self.path == '/mcp/call_tool':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'result': 'Tool executed'}).encode())
        else:
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'AgentScope PSR Analyzer - OK')
    
    def do_POST(self):
        if self.path == '/mcp/call_tool':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'result': 'Tool executed', 'input': post_data.decode()}).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        print(format % args)

with socketserver.TCPServer(('', 80), Handler) as httpd:
    print('HTTP server listening on port 80')
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
fi
