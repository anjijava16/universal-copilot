#!/bin/bash

# Install all MCP servers
echo "📦 Installing all MCP servers..."

for dir in */; do
    if [ -f "$dir/requirements.txt" ]; then
        echo "Installing $dir..."
        cd "$dir"
        pip install -r requirements.txt
        cd ..
    fi
done

echo "✅ All servers installed successfully!"
