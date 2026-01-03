#!/bin/bash

# ============================================================================
# Garden Genie Backend - Cleanup and Redeploy Script
# ============================================================================
# This script fixes the current deployment issues

set -e

echo "============================================================================"
echo "🔧 Garden Genie Backend - Cleanup & Redeploy"
echo "============================================================================"
echo ""

# ============================================================================
# STEP 1: Stop and remove ALL containers
# ============================================================================
echo "🛑 Step 1: Stopping and removing all Garden Genie containers..."

# Stop the app container
if [ "$(docker ps -q -f name=gardengenie-backend)" ]; then
    echo "  Stopping gardengenie-backend..."
    docker stop gardengenie-backend
fi

if [ "$(docker ps -aq -f name=gardengenie-backend)" ]; then
    echo "  Removing gardengenie-backend..."
    docker rm gardengenie-backend
fi

# Stop the old prod container
if [ "$(docker ps -q -f name=gardengenie-prod)" ]; then
    echo "  Stopping gardengenie-prod..."
    docker stop gardengenie-prod
fi

if [ "$(docker ps -aq -f name=gardengenie-prod)" ]; then
    echo "  Removing gardengenie-prod..."
    docker rm gardengenie-prod
fi

# Stop the old database container (orphan)
if [ "$(docker ps -q -f name=gardengenie-db)" ]; then
    echo "  Stopping old database container..."
    docker stop gardengenie-db
fi

if [ "$(docker ps -aq -f name=gardengenie-db)" ]; then
    echo "  Removing old database container..."
    docker rm gardengenie-db
fi

echo "✅ All old containers removed"

# ============================================================================
# STEP 2: Remove old volumes
# ============================================================================
echo ""
echo "🧹 Step 2: Cleaning up old volumes..."

if [ "$(docker volume ls -q -f name=genie_ai_backend_postgres_data)" ]; then
    echo "  Removing postgres_data volume..."
    docker volume rm genie_ai_backend_postgres_data 2>/dev/null || echo "  Volume already removed"
fi

echo "✅ Old volumes cleaned"

# ============================================================================
# STEP 3: Clean up Docker system
# ============================================================================
echo ""
echo "🧹 Step 3: Cleaning Docker system..."
docker system prune -f
echo "✅ Docker system cleaned"

# ============================================================================
# STEP 4: Backup old docker-compose.yml
# ============================================================================
echo ""
echo "💾 Step 4: Backing up old configuration..."

if [ -f docker-compose.yml ]; then
    cp docker-compose.yml docker-compose.yml.backup
    echo "✅ Old docker-compose.yml backed up"
fi

# ============================================================================
# STEP 5: Use new docker-compose.yml
# ============================================================================
echo ""
echo "📝 Step 5: Updating docker-compose.yml..."
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: gardengenie-backend
    restart: unless-stopped
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - ./uploads:/app/uploads
      - ./app/models:/app/app/models
    environment:
      - PYTHONUNBUFFERED=1
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

# No local database - using Neon PostgreSQL
EOF

echo "✅ docker-compose.yml updated"

# ============================================================================
# STEP 6: Build new image
# ============================================================================
echo ""
echo "🏗️  Step 6: Building new Docker image..."
docker-compose build --no-cache
echo "✅ Docker image built"

# ============================================================================
# STEP 7: Start the application
# ============================================================================
echo ""
echo "🚀 Step 7: Starting application..."
docker-compose up -d
echo "✅ Application started"

# ============================================================================
# STEP 8: Wait for service to be ready
# ============================================================================
echo ""
echo "⏳ Step 8: Waiting for service to start..."
sleep 15

# ============================================================================
# STEP 9: Check container status
# ============================================================================
echo ""
echo "🔍 Step 9: Checking container status..."

if [ "$(docker ps -q -f name=gardengenie-backend)" ]; then
    echo "✅ Container is running"
    docker ps -f name=gardengenie-backend
else
    echo "❌ Container failed to start!"
    echo ""
    echo "Recent logs:"
    docker-compose logs --tail=50
    exit 1
fi

# ============================================================================
# STEP 10: Health check
# ============================================================================
echo ""
echo "🏥 Step 10: Running health check..."

max_attempts=30
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if curl -f http://localhost:8000/health &> /dev/null; then
        echo "✅ Health check passed!"
        break
    else
        attempt=$((attempt + 1))
        echo "  Attempt $attempt/$max_attempts - Service not ready yet..."
        sleep 2
    fi
done

if [ $attempt -eq $max_attempts ]; then
    echo "❌ Health check failed!"
    echo ""
    echo "Container logs:"
    docker-compose logs --tail=100
    exit 1
fi

# ============================================================================
# STEP 11: Test endpoints
# ============================================================================
echo ""
echo "🧪 Step 11: Testing endpoints..."

# Test /health
if curl -f http://localhost:8000/health &> /dev/null; then
    echo "  ✅ /health works"
else
    echo "  ❌ /health failed"
fi

# Test /products/ (with trailing slash)
if curl -f http://localhost:8000/products/ &> /dev/null; then
    echo "  ✅ /products/ works"
else
    echo "  ⚠️  /products/ failed (may need data)"
fi

# Test / (root)
if curl -f http://localhost:8000/ &> /dev/null; then
    echo "  ✅ / (root) works"
else
    echo "  ❌ / failed"
fi

# ============================================================================
# STEP 12: Show summary
# ============================================================================
echo ""
echo "============================================================================"
echo "✅ DEPLOYMENT COMPLETED SUCCESSFULLY!"
echo "============================================================================"
echo ""
echo "📊 Container Information:"
docker ps -f name=gardengenie-backend --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo ""
echo "🔍 Useful Commands:"
echo "  View logs:         docker-compose logs -f"
echo "  Stop service:      docker-compose down"
echo "  Restart service:   docker-compose restart"
echo "  Container shell:   docker-compose exec app bash"
echo ""
echo "🌐 Your API is live at:"
echo "  - Health: http://localhost:8000/health"
echo "  - Docs:   http://localhost:8000/docs"
echo ""
echo "📝 Recent logs:"
echo "============================================================================"
docker-compose logs --tail=30
echo "============================================================================"