"""
Example client for testing MCP servers
"""

import asyncio
import httpx
from typing import Dict, Any


class MCPClient:
    """Simple HTTP client for MCP servers"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def call_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool on the MCP server"""
        url = f"{self.base_url}/tools/{tool_name}"
        response = await self.client.post(url, json=params)
        response.raise_for_status()
        return response.json()
    
    async def list_tools(self) -> Dict[str, Any]:
        """List available tools"""
        url = f"{self.base_url}/tools"
        response = await self.client.get(url)
        response.raise_for_status()
        return response.json()
    
    async def health_check(self) -> Dict[str, Any]:
        """Check server health"""
        url = f"{self.base_url}/health"
        response = await self.client.get(url)
        response.raise_for_status()
        return response.json()
    
    async def close(self):
        """Close the client"""
        await self.client.aclose()


async def test_file_directory_server():
    """Test File & Directory Management Server"""
    print("\n🧪 Testing File & Directory Management Server (Port 8001)")
    
    client = MCPClient("http://localhost:8001")
    
    try:
        # Health check
        health = await client.health_check()
        print(f"✅ Health: {health}")
        
        # List tools
        tools = await client.list_tools()
        print(f"📋 Available tools: {len(tools.get('tools', []))}")
        
        # Test create_directory
        result = await client.call_tool("create_directory", {
            "dirPath": "/tmp/mcp_test"
        })
        print(f"📂 Create directory: {result}")
        
        # Test create_file
        result = await client.call_tool("create_file", {
            "filePath": "/tmp/mcp_test/hello.txt",
            "content": "Hello from MCP!"
        })
        print(f"📝 Create file: {result}")
        
        # Test list_dir
        result = await client.call_tool("list_dir", {
            "path": "/tmp/mcp_test"
        })
        print(f"📋 List directory: {result}")
        
        # Test file_search
        result = await client.call_tool("file_search", {
            "query": "/tmp/mcp_test/**/*.txt"
        })
        print(f"🔍 File search: {result}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await client.close()


async def test_memory_server():
    """Test Memory Management Server"""
    print("\n🧪 Testing Memory Management Server (Port 8007)")
    
    client = MCPClient("http://localhost:8007")
    
    try:
        # Create memory
        result = await client.call_tool("memory", {
            "command": "create",
            "path": "/memories/test.md",
            "file_text": "# Test Memory\n\nThis is a test."
        })
        print(f"🧠 Create memory: {result}")
        
        # View memory
        result = await client.call_tool("memory", {
            "command": "view",
            "path": "/memories/test.md"
        })
        print(f"👁️  View memory: {result}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await client.close()


async def test_task_todo_server():
    """Test Task & Todo Management Server"""
    print("\n🧪 Testing Task & Todo Management Server (Port 8008)")
    
    client = MCPClient("http://localhost:8008")
    
    try:
        # Manage todo list
        result = await client.call_tool("manage_todo_list", {
            "todoList": [
                {"id": 1, "title": "Setup project", "status": "completed"},
                {"id": 2, "title": "Write tests", "status": "in-progress"},
                {"id": 3, "title": "Deploy", "status": "not-started"}
            ]
        })
        print(f"✅ Manage todos: {result}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await client.close()


async def test_python_env_server():
    """Test Python Environment Management Server"""
    print("\n🧪 Testing Python Environment Management Server (Port 8012)")
    
    client = MCPClient("http://localhost:8012")
    
    try:
        # Configure environment
        result = await client.call_tool("configure_python_environment", {
            "resourcePath": "/tmp/test_project"
        })
        print(f"🐍 Configure environment: {result}")
        
        # Install packages
        result = await client.call_tool("install_python_packages", {
            "packageList": ["requests", "pytest"],
            "resourcePath": "/tmp/test_project"
        })
        print(f"📦 Install packages: {result}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await client.close()


async def main():
    """Run all tests"""
    print("🚀 MCP Servers Client Test Suite")
    print("=" * 50)
    
    # Test individual servers
    await test_file_directory_server()
    await test_memory_server()
    await test_task_todo_server()
    await test_python_env_server()
    
    print("\n" + "=" * 50)
    print("✅ All tests completed!")


if __name__ == "__main__":
    asyncio.run(main())
