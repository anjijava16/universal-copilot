#!/bin/bash

# Test all MCP servers
echo "🧪 Testing all MCP servers..."

failed=0
passed=0

for dir in */; do
    if [ -f "$dir/server.py" ]; then
        server_name=$(basename "$dir")
        echo "Testing $server_name..."
        
        cd "$dir"
        if [ -d "tests" ]; then
            pytest tests/ -v
            if [ $? -eq 0 ]; then
                ((passed++))
                echo "✅ $server_name tests passed"
            else
                ((failed++))
                echo "❌ $server_name tests failed"
            fi
        else
            echo "⚠️  No tests found for $server_name"
        fi
        cd ..
    fi
done

echo ""
echo "📊 Test Results:"
echo "   Passed: $passed"
echo "   Failed: $failed"

if [ $failed -eq 0 ]; then
    echo "✅ All tests passed!"
    exit 0
else
    echo "❌ Some tests failed"
    exit 1
fi
