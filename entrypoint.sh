#!/bin/bash
# AgentScope PSR Analyzer Entrypoint
# Supports both HTTP service mode (AgentScope) and CLI mode
# Build trigger: 2026-03-23 21:45 - ACR rebuild
# Rebuild: 2026-03-23 22:50 - Fix HTTP endpoint routing
# Rebuild: 2026-03-24 11:05 - Fix endpoint matching logic
# Rebuild: 2026-03-24 14:15 - Add MCP /call_tool endpoint support

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
import traceback
import datetime

class AgentScopeHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Log with timestamp for debugging
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        sys.stderr.write('[%s] %s\n' % (timestamp, format % args))
        sys.stderr.flush()
    
    def do_GET(self):
        if self.path == '/fastapi/healthz' or self.path == '/healthz':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'healthy'}).encode())
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'Not found'}).encode())
    
    def do_POST(self):
        # Support both old and new AgentScope endpoints
        if self.path.endswith('/tools/run_shell_command'):
            self._handle_run_shell_command()
        elif self.path.endswith('/mcp/call_tool'):
            self._handle_call_tool()
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'Not found'}).encode())
    
    def _handle_run_shell_command(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            request_body_str = post_data.decode('utf-8')
            
            # Log full request for debugging
            self.log_message('=== TOOL REQUEST ===')
            self.log_message('Path: %s', self.path)
            self.log_message('Headers: %s', dict(self.headers))
            self.log_message('Body: %s', request_body_str)
            
            request_data = json.loads(request_body_str)
            
            arguments = request_data.get('arguments', {})
            command = arguments.get('command', '')
            
            if not command:
                command = arguments.get('cmd', '')
                if not command:
                    command = request_data.get('command', '')
            
            self.log_message('Executing command: %s', command)
            
            if command:
                result = subprocess.run(command, shell=True, capture_output=True, text=True)
                self.log_message('Command returncode: %d', result.returncode)
                self.log_message('Command stdout: %s', result.stdout)
                self.log_message('Command stderr: %s', result.stderr)
                
                response = {
                    'result': result.stdout if result.returncode == 0 else result.stderr,
                    'returncode': result.returncode,
                    'success': result.returncode == 0
                }
            else:
                self.log_message('ERROR: No command provided')
                response = {
                    'error': 'No command provided in request',
                    'success': False
                }
            
            self.log_message('Response: %s', json.dumps(response))
            self.log_message('=== END REQUEST ===')
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            self.log_message('Exception: %s', str(e))
            self.log_message('Traceback: %s', traceback.format_exc())
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            error_msg = f'Error executing command: {str(e)}'
            self.wfile.write(json.dumps({'error': error_msg, 'success': False}).encode())
    
    def _handle_call_tool(self):
        # AgentScope MCP /call_tool endpoint
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            request_body_str = post_data.decode('utf-8')
            
            # Log full request for debugging
            self.log_message('=== MCP CALL_TOOL REQUEST ===')
            self.log_message('Path: %s', self.path)
            self.log_message('Headers: %s', dict(self.headers))
            self.log_message('Body: %s', request_body_str)
            
            request_data = json.loads(request_body_str)
            
            tool_name = request_data.get('tool_name', '')
            arguments = request_data.get('arguments', {})
            
            self.log_message('Tool name: %s', tool_name)
            self.log_message('Arguments: %s', json.dumps(arguments))
            
            if tool_name == 'run_shell_command':
                command = arguments.get('command', '')
                if command:
                    self.log_message('Executing command: %s', command)
                    result = subprocess.run(command, shell=True, capture_output=True, text=True)
                    self.log_message('Command returncode: %d', result.returncode)
                    self.log_message('Command stdout: %s', result.stdout)
                    self.log_message('Command stderr: %s', result.stderr)
                    
                    response = {
                        'result': result.stdout if result.returncode == 0 else result.stderr,
                        'returncode': result.returncode,
                        'success': result.returncode == 0
                    }
                else:
                    self.log_message('ERROR: No command provided')
                    response = {
                        'error': 'No command provided',
                        'success': False
                    }
            else:
                self.log_message('ERROR: Unknown tool: %s', tool_name)
                response = {
                    'error': f'Unknown tool: {tool_name}',
                    'success': False
                }
            
            self.log_message('Response: %s', json.dumps(response))
            self.log_message('=== END REQUEST ===')
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            self.log_message('Exception: %s', str(e))
            self.log_message('Traceback: %s', traceback.format_exc())
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            error_msg = f'Error calling tool: {str(e)}'
            self.wfile.write(json.dumps({'error': error_msg, 'success': False}).encode())

with socketserver.TCPServer(('', 80), AgentScopeHandler) as httpd:
    print('HTTP server listening on port 80')
    print('Available endpoints:')
    print('  GET  /fastapi/healthz')
    print('  POST /fastapi/tools/run_shell_command')
    print('  POST /mcp/call_tool')
    sys.stdout.flush()
    httpd.serve_forever()
"
    fi
else
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
            echo "  fetch --date_range START~END"
            echo "  analyze --date YYYYMMDD"
            echo "  send --date YYYYMMDD --recipient email@example.com"
            exit 1
            ;;
    esac
fi
