#!/bin/bash
# AgentScope PSR Analyzer Entrypoint
# Supports both HTTP service mode (AgentScope) and CLI mode

# If no arguments or first arg starts with "--", start HTTP service (AgentScope mode)
if [ $# -eq 0 ] || [[ "$1" == --* ]] || [ "$1" = "serve" ]; then
    # Start HTTP service for AgentScope
    echo "Starting AgentScope HTTP service on port 80..."
    exec python3 -c "
import http.server
import socketserver
import json
import sys
import subprocess
import urllib.parse

class AgentScopeHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        # Health check endpoint
        if self.path == '/fastapi/healthz' or self.path == '/healthz':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'healthy'}).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        # Tool execution endpoint
        if self.path == '/fastapi/tools/run_shell_command' or self.path == '/tools/run_shell_command':
            try:
                # Read request body
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length)
                request_data = json.loads(post_data.decode('utf-8'))
                
                print(f'Received tool call: {request_data}', file=sys.stderr)
                
                # Extract command from the request
                # Expected format: {
                #   "tool_name": "run_shell_command",
                #   "arguments": {"command": "python3 /app/query_antom_psr_data.py --date 20250323"}
                # }
                arguments = request_data.get('arguments', {})
                command = arguments.get('command', '')
                
                if not command:
                    # Try alternative format: {"cmd": "..."}
                    command = arguments.get('cmd', '')
                
                if command:
                    print(f'Executing command: {command}', file=sys.stderr)
                    # Execute the command
                    result = subprocess.run(command, shell=True, capture_output=True, text=True)
                    
                    response = {
                        'result': result.stdout if result.returncode == 0 else result.stderr,
                        'returncode': result.returncode,
                        'success': result.returncode == 0
                    }
                else:
                    response = {
                        'error': 'No command provided',
                        'success': False
                    }
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode())
                
            except Exception as e:
                print(f'Error processing request: {e}', file=sys.stderr)
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e), 'success': False}).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        # Custom logging
        print(f'[HTTP] {format % args}', file=sys.stderr)

with socketserver.TCPServer(('', 80), AgentScopeHandler) as httpd:
    print('HTTP server listening on port 80')
    print('Endpoints:')
    print('  GET  /fastapi/healthz')
    print('  POST /fastapi/tools/run_shell_command')
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
