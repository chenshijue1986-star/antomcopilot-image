#!/bin/bash
# AgentScope PSR Analyzer Entrypoint
# Supports both HTTP service mode (AgentScope) and CLI mode
# Build trigger: 2026-03-23 21:45 - ACR rebuild
# Rebuild: 2026-03-23 22:50 - Fix HTTP endpoint routing

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
import traceback

class AgentScopeHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        # Health check endpoint
        if self.path == '/fastapi/healthz' or self.path == '/healthz':
            self.log_message('Health check from %s', self.client_address)
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'healthy'}).encode())
        else:
            self.log_message('GET %s - 404', self.path)
            self.send_response(404)
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'Not found'}).encode())
    
    def do_POST(self):
        self.log_message('POST %s from %s', self.path, self.client_address)
        # Tool execution endpoint
        if '/tools/run_shell_command' in self.path:
            try:
                # Read request body
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length)
                self.log_message('Request body: %s', post_data.decode('utf-8'))
                
                request_data = json.loads(post_data.decode('utf-8'))
                self.log_message('Parsed JSON: %s', request_data)
                
                # Extract command from the request
                # Expected format: {
                #   "tool_name": "run_shell_command",
                #   "arguments": {"command": "python3 /app/query_antom_psr_data.py --date 20250323"}
                # }
                arguments = request_data.get('arguments', {})
                command = arguments.get('command', '')
                
                if not command:
                    # Try another format or direct command
                    command = arguments.get('cmd', '')
                    if not command:
                        command = request_data.get('command', '')
                
                self.log_message('Executing command: %s', command)
                
                if command:
                    # Execute the command
                    result = subprocess.run(command, shell=True, capture_output=True, text=True)
                    
                    response = {
                        'result': result.stdout if result.returncode == 0 else result.stderr,
                        'returncode': result.returncode,
                        'success': result.returncode == 0
                    }
                else:
                    response = {
                        'error': 'No command provided in request',
                        'success': False
                    }
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode())
                
            except Exception as e:
                self.log_message('Error processing request: %s', traceback.format_exc())
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                error_msg = f'Error executing command: {str(e)}'
                self.wfile.write(json.dumps({'error': error_msg, 'success': False}).encode())
        else:
            self.log_message('POST %s - 404', self.path)
            self.send_response(404)
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'Not found'}).encode())
    
    def log_message(self, format, *args):
        # Custom logging to stderr
        print(f'[HTTP Server] {format % args}', file=sys.stderr)

with socketserver.TCPServer(('', 80), AgentScopeHandler) as httpd:
    print('HTTP server listening on port 80')
    print('Available endpoints:')
    print('  GET  /fastapi/healthz')
    print('  GET  /healthz')
    print('  POST /fastapi/tools/run_shell_command')
    print('  POST /tools/run_shell_command')
    sys.stdout.flush()
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
