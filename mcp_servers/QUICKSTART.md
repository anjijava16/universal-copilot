# Quick Start Guide 🚀

Get up and running with MCP Servers in 5 minutes!

## Prerequisites

- Python 3.9 or higher
- pip or uv package manager
- (Optional) Docker and Docker Compose

## Installation

### Option 1: Local Installation

```bash
# Clone the repository
git clone <repository-url>
cd mcp_servers

# Install all servers
chmod +x install_all.sh
./install_all.sh

# Or install individual server
cd 01-mcp-file-directory-server
pip install -r requirements.txt
```

### Option 2: Docker Installation

```bash
# Copy environment variables
cp .env.example .env

# Edit .env with your credentials
nano .env

# Start all servers
docker-compose up -d

# Check status
docker-compose ps
```

## Running Servers

### Start Individual Server

```bash
cd 01-mcp-file-directory-server
python server.py
```

Output:
```
🚀 Starting File & Directory Management MCP Server...
📂 Workspace root: /path/to/workspace
📡 Port: 8001
✅ Server ready!
```

### Start All Servers

```bash
# Create logs directory
mkdir -p logs

# Start all servers
chmod +x run_all.sh
./run_all.sh
```

## Testing

### Quick Health Check

```bash
# Test File & Directory Server
curl http://localhost:8001/health

# Expected response:
# {"status": "healthy", "server": "File & Directory Management Server"}
```

### List Available Tools

```bash
curl http://localhost:8001/tools
```

### Call a Tool

```bash
# Create a directory
curl -X POST http://localhost:8001/tools/create_directory \
  -H "Content-Type: application/json" \
  -d '{"dirPath": "/tmp/test_mcp"}'

# Expected response:
# {
#   "success": true,
#   "path": "/tmp/test_mcp",
#   "message": "Directory created successfully"
# }
```

### Run Test Suite

```bash
# Install test dependencies
pip install pytest httpx

# Run client tests
python client_example.py

# Run all server tests
chmod +x test_all.sh
./test_all.sh
```

## Usage Examples

### Example 1: File Operations

```python
import asyncio
import httpx

async def create_project_structure():
    client = httpx.AsyncClient()
    
    # Create directories
    await client.post("http://localhost:8001/tools/create_directory", 
        json={"dirPath": "./my_project/src"})
    await client.post("http://localhost:8001/tools/create_directory", 
        json={"dirPath": "./my_project/tests"})
    
    # Create files
    await client.post("http://localhost:8001/tools/create_file", json={
        "filePath": "./my_project/src/main.py",
        "content": "def main():\n    print('Hello, World!')\n"
    })
    
    # List directory
    response = await client.post("http://localhost:8001/tools/list_dir",
        json={"path": "./my_project"})
    print(response.json())
    
    await client.aclose()

asyncio.run(create_project_structure())
```

### Example 2: Memory Management

```python
import asyncio
import httpx

async def manage_memory():
    client = httpx.AsyncClient()
    
    # Create memory note
    await client.post("http://localhost:8007/tools/memory", json={
        "command": "create",
        "path": "/memories/project_notes.md",
        "file_text": "# Project Notes\n\n- Task 1: Complete\n- Task 2: In Progress"
    })
    
    # View memory
    response = await client.post("http://localhost:8007/tools/memory",
        json={"command": "view", "path": "/memories/project_notes.md"})
    print(response.json())
    
    await client.aclose()

asyncio.run(manage_memory())
```

### Example 3: Task Management

```python
import asyncio
import httpx

async def manage_tasks():
    client = httpx.AsyncClient()
    
    # Create todo list
    response = await client.post("http://localhost:8008/tools/manage_todo_list", json={
        "todoList": [
            {"id": 1, "title": "Setup environment", "status": "completed"},
            {"id": 2, "title": "Write code", "status": "in-progress"},
            {"id": 3, "title": "Deploy", "status": "not-started"}
        ]
    })
    print(response.json())
    
    await client.aclose()

asyncio.run(manage_tasks())
```

### Example 4: Python Environment

```python
import asyncio
import httpx

async def setup_python_env():
    client = httpx.AsyncClient()
    
    # Configure environment
    await client.post("http://localhost:8012/tools/configure_python_environment",
        json={"resourcePath": "./my_project"})
    
    # Install packages
    response = await client.post("http://localhost:8012/tools/install_python_packages", json={
        "packageList": ["requests", "pytest", "black"],
        "resourcePath": "./my_project"
    })
    print(response.json())
    
    await client.aclose()

asyncio.run(setup_python_env())
```

## Integration with VS Code

### Configure MCP in VS Code

1. Install the MCP extension for VS Code
2. Add server configuration to `.vscode/mcp.json`:

```json
{
  "mcpServers": {
    "file-directory": {
      "command": "python",
      "args": ["path/to/01-mcp-file-directory-server/server.py"],
      "env": {
        "PORT": "8001"
      }
    },
    "file-operations": {
      "command": "python",
      "args": ["path/to/02-mcp-file-operations-server/server.py"],
      "env": {
        "PORT": "8002"
      }
    }
  }
}
```

3. Restart VS Code
4. Use Copilot with MCP tools!

## Troubleshooting

### Port Already in Use

```bash
# Find process using port
lsof -i :8001

# Kill process
kill -9 <PID>

# Or use different port
PORT=9001 python server.py
```

### Module Not Found

```bash
# Reinstall dependencies
pip install -r requirements.txt

# Or use virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Connection Refused

```bash
# Check if server is running
ps aux | grep server.py

# Check logs
tail -f logs/01-mcp-file-directory-server.log

# Restart server
pkill -f server.py
python server.py
```

### Docker Issues

```bash
# Rebuild containers
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# View logs
docker-compose logs -f mcp-file-directory

# Check container status
docker-compose ps
```

## Next Steps

1. **Explore Tools**: Check each server's README for detailed tool documentation
2. **Customize**: Modify server.py files to add custom logic
3. **Integrate**: Connect servers to your applications
4. **Monitor**: Set up logging and metrics
5. **Deploy**: Use Docker Compose or Kubernetes for production

## Resources

- [Full Documentation](./README.md)
- [Architecture Guide](./ARCHITECTURE.md)
- [API Reference](./vscode/tools_catalog.md)
- [FastMCP Docs](https://github.com/jlowin/fastmcp)
- [MCP Specification](https://modelcontextprotocol.io)

## Support

- GitHub Issues: <repository-url>/issues
- Discord: <discord-invite>
- Email: support@example.com

---

**Happy Coding! 🎉**
