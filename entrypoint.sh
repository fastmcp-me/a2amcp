#!/bin/bash
set -e

echo "Starting SplitMind MCP Agent Communication Server..."
echo "Redis URL: ${REDIS_URL}"
echo "Log Level: ${LOG_LEVEL}"

# Wait for Redis to be ready
echo "Waiting for Redis..."
until python -c "import redis; r = redis.from_url('${REDIS_URL}'); r.ping()" 2>/dev/null; do
    echo "Redis is unavailable - sleeping"
    sleep 1
done

echo "Redis is ready!"

# Start a simple HTTP health check server in the background
python -c "
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import redis
import os

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            try:
                # Check Redis connection
                r = redis.from_url(os.getenv('REDIS_URL', 'redis://redis:6379'))
                r.ping()
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {
                    'status': 'healthy',
                    'service': 'splitmind-mcp-server',
                    'redis': 'connected'
                }
                self.wfile.write(json.dumps(response).encode())
            except Exception as e:
                self.send_response(503)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {
                    'status': 'unhealthy',
                    'service': 'splitmind-mcp-server',
                    'error': str(e)
                }
                self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        # Suppress logs except for errors
        if args[1] != '200':
            super().log_message(format, *args)

print('Starting health check server on port 5000...')
httpd = HTTPServer(('', 5000), HealthHandler)
httpd.serve_forever()
" &

# For MCP servers that communicate via STDIO, we need to keep the container running
# The actual MCP server will be invoked by Claude when needed
echo "MCP Server is ready and waiting for STDIO connections..."
echo "Connect via Claude Desktop or Claude Code MCP configuration"
echo "Health check available at http://localhost:5050/health"

# Keep the container running
tail -f /dev/null