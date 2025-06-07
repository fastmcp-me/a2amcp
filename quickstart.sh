#!/bin/bash
# SplitMind MCP Server Quick Start Script

set -e

echo "🚀 SplitMind MCP Agent Communication Server Setup"
echo "================================================"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p logs

# Make entrypoint executable
echo "🔧 Setting permissions..."
chmod +x entrypoint.sh

# Build and start services
echo "🏗️  Building Docker images..."
docker-compose build

echo "🚀 Starting services..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 5

# Check service health
echo "🏥 Checking service health..."
if docker-compose ps | grep -q "Up"; then
    echo "✅ Services are running!"
else
    echo "❌ Services failed to start. Check logs with: docker-compose logs"
    exit 1
fi

# Show service status
echo ""
echo "📊 Service Status:"
docker-compose ps

echo ""
echo "🎉 SplitMind MCP Server is ready!"
echo ""
echo "📍 Service URLs:"
echo "   - MCP Server: localhost:5000"
echo "   - Redis: localhost:6379"
echo ""
echo "📝 Useful commands:"
echo "   - View logs: docker-compose logs -f"
echo "   - Stop services: docker-compose down"
echo "   - Start with monitoring: docker-compose --profile debug up -d"
echo "   - Redis CLI: docker exec -it splitmind-redis redis-cli"
echo ""
echo "🔌 Configure your Claude Code agents to connect to the MCP server"
echo "   by adding the server configuration to their MCP settings."
echo ""
echo "📚 See README.md for detailed documentation and examples."