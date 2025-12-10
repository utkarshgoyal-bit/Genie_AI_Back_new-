#!/bin/bash

echo "🔍 Verifying migration..."

# Check new file structure
echo ""
echo "1️⃣ Checking new files exist..."
files=(
    "app/models.py"
    "app/utils.py"
    "app/domains/analyze.py"
    "app/domains/products.py"
    "app/domains/auth.py"
    "app/domains/history.py"
    "app/main.py"
)

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✅ $file"
    else
        echo "  ❌ MISSING: $file"
    fi
done

# Check old files are deleted
echo ""
echo "2️⃣ Checking old files are deleted..."
old_dirs=(
    "app/config"
    "app/controllers"
    "app/routes"
)

for dir in "${old_dirs[@]}"; do
    if [ ! -d "$dir" ]; then
        echo "  ✅ $dir removed"
    else
        echo "  ⚠️  $dir still exists (should be deleted)"
    fi
done

# Test API endpoints
echo ""
echo "3️⃣ Testing API endpoints..."
echo "  Starting server in background..."
python app/main.py &
SERVER_PID=$!
sleep 5

# Test health endpoint
response=$(curl -s http://localhost:8000/health)
if [[ $response == *"healthy"* ]]; then
    echo "  ✅ Health endpoint works"
else
    echo "  ❌ Health endpoint failed"
fi

# Test root endpoint
response=$(curl -s http://localhost:8000/)
if [[ $response == *"Plant Disease Detection API"* ]]; then
    echo "  ✅ Root endpoint works"
else
    echo "  ❌ Root endpoint failed"
fi

# Kill server
kill $SERVER_PID

echo ""
echo "✅ Migration verification complete!"
