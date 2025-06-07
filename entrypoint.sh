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

# Run the MCP server
exec python mcp_server_redis.py