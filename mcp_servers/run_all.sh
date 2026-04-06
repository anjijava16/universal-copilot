#!/bin/bash

# Run all MCP servers in background
echo "🚀 Starting all MCP servers..."

# Array to store PIDs
declare -a PIDS

# Function to cleanup on exit
cleanup() {
    echo "🛑 Stopping all servers..."
    for pid in "${PIDS[@]}"; do
        kill $pid 2>/dev/null
    done
    exit 0
}

# Trap SIGINT and SIGTERM
trap cleanup SIGINT SIGTERM

# Start each server
for dir in */; do
    if [ -f "$dir/server.py" ]; then
        server_name=$(basename "$dir")
        echo "Starting $server_name..."
        cd "$dir"
        python3 server.py > "../logs/${server_name}.log" 2>&1 &
        PIDS+=($!)
        cd ..
        sleep 1
    fi
done

echo "✅ All servers started!"
echo "📋 Server PIDs: ${PIDS[@]}"
echo "📝 Logs directory: ./logs/"
echo "Press Ctrl+C to stop all servers"

# Wait for all background processes
wait
