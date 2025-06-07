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

# For MCP servers that communicate via STDIO, we need to keep the container running
# The actual MCP server will be invoked by Claude when needed
echo "MCP Server is ready and waiting for STDIO connections..."
echo "Connect via Claude Desktop or Claude Code MCP configuration"

# Keep the container running
tail -f /dev/null