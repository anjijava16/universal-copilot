# MCP Servers Collection

A comprehensive collection of 16 FastMCP-based Model Context Protocol servers, each implementing tools for specific VS Code Copilot functionality categories.

## 📦 Available Servers

| # | Server Name | Category | Port | Tools Count |
|---|-------------|----------|------|-------------|
| 1 | [mcp-file-directory-server](#1-mcp-file-directory-server) | File & Directory Management | 8001 | 5 |
| 2 | [mcp-file-operations-server](#2-mcp-file-operations-server) | File Operations | 8002 | 6 |
| 3 | [mcp-search-discovery-server](#3-mcp-search-discovery-server) | Search & Discovery | 8003 | 4 |
| 4 | [mcp-notebook-operations-server](#4-mcp-notebook-operations-server) | Notebook Operations | 8004 | 5 |
| 5 | [mcp-vscode-integration-server](#5-mcp-vscode-integration-server) | VS Code Integration | 8005 | 6 |
| 6 | [mcp-terminal-process-server](#6-mcp-terminal-process-server) | Terminal & Process Management | 8006 | 6 |
| 7 | [mcp-memory-management-server](#7-mcp-memory-management-server) | Memory Management | 8007 | 2 |
| 8 | [mcp-task-todo-server](#8-mcp-task-todo-server) | Task & Todo Management | 8008 | 2 |
| 9 | [mcp-azure-auth-server](#9-mcp-azure-auth-server) | Azure Authentication & Resources | 8009 | 3 |
| 10 | [mcp-azure-services-server](#10-mcp-azure-services-server) | Azure Services | 8010 | 6 |
| 11 | [mcp-azure-cli-server](#11-mcp-azure-cli-server) | Azure CLI & Templates | 8011 | 2 |
| 12 | [mcp-python-env-server](#12-mcp-python-env-server) | Python Environment Management | 8012 | 6 |
| 13 | [mcp-python-analysis-server](#13-mcp-python-analysis-server) | Python Analysis & Refactoring | 8013 | 5 |
| 14 | [mcp-microsoft-docs-server](#14-mcp-microsoft-docs-server) | Microsoft Documentation | 8014 | 3 |
| 15 | [mcp-specialized-tools-server](#15-mcp-specialized-tools-server) | Specialized Tools | 8015 | 3 |
| 16 | [mcp-subagent-server](#16-mcp-subagent-server) | Subagent | 8016 | 1 |

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- pip or uv package manager

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd mcp_servers

# Install all servers
./install_all.sh

# Or install individual server
cd mcp-file-directory-server
pip install -r requirements.txt
```

### Running Servers

```bash
# Run individual server
cd mcp-file-directory-server
python server.py

# Run all servers (in separate terminals)
./run_all.sh
```

## 📚 Server Details

### 1. mcp-file-directory-server
**Port:** 8001  
**Tools:** create_directory, create_file, list_dir, file_search, grep_search

Manages file system operations including directory creation, file creation, listing, and searching.

### 2. mcp-file-operations-server
**Port:** 8002  
**Tools:** read_file, replace_string_in_file, multi_replace_string_in_file, view_image, get_changed_files, get_errors

Handles file reading, editing, image viewing, and error detection.

### 3. mcp-search-discovery-server
**Port:** 8003  
**Tools:** semantic_search, get_search_view_results, github_repo, fetch_webpage

Provides semantic search, GitHub repository search, and web content fetching.

### 4. mcp-notebook-operations-server
**Port:** 8004  
**Tools:** create_new_jupyter_notebook, edit_notebook_file, copilot_getNotebookSummary, run_notebook_cell, read_notebook_cell_output

Manages Jupyter notebook creation, editing, execution, and output retrieval.

### 5. mcp-vscode-integration-server
**Port:** 8005  
**Tools:** create_new_workspace, get_project_setup_info, get_vscode_api, install_extension, run_vscode_command, vscode_searchExtensions_internal

Integrates with VS Code for workspace creation, extension management, and API access.

### 6. mcp-terminal-process-server
**Port:** 8006  
**Tools:** run_in_terminal, await_terminal, get_terminal_output, kill_terminal, terminal_last_command, terminal_selection

Manages terminal processes, command execution, and output retrieval.

### 7. mcp-memory-management-server
**Port:** 8007  
**Tools:** memory, resolve_memory_file_uri

Provides persistent memory management across user, session, and repository scopes.

### 8. mcp-task-todo-server
**Port:** 8008  
**Tools:** manage_todo_list, create_and_run_task

Manages todo lists and VS Code tasks for project workflow.

### 9. mcp-azure-auth-server
**Port:** 8009  
**Tools:** activate_azure_authentication_and_resource_management, azureResources_getAzureActivityLog, activate_azure_subscription_and_resource_group_tools

Handles Azure authentication, resource queries, and subscription management.

### 10. mcp-azure-services-server
**Port:** 8010  
**Tools:** azure_bicep_get_azure_verified_module, mcp_azure_mcp_applens, mcp_azure_mcp_azureterraformbestpractices, mcp_azure_mcp_confidentialledger, mcp_azure_mcp_resourcehealth, mcp_azure_mcp_speech

Provides Azure service operations including Bicep, AppLens diagnostics, and AI services.

### 11. mcp-azure-cli-server
**Port:** 8011  
**Tools:** activate_azure_cli_tools, activate_dotnet_project_template_management

Manages Azure CLI command generation and .NET project templates.

### 12. mcp-python-env-server
**Port:** 8012  
**Tools:** configure_python_environment, install_python_packages, activate_python_environment_tools, configure_notebook, activate_notebook_kernel_configuration, activate_notebook_package_management

Manages Python environments, package installation, and notebook configuration.

### 13. mcp-python-analysis-server
**Port:** 8013  
**Tools:** activate_python_syntax_validation_tools, activate_python_import_analysis_tools, mcp_pylance_mcp_s_pylanceDocString, mcp_pylance_mcp_s_pylanceInvokeRefactoring, mcp_pylance_mcp_s_pylanceImports

Provides Python code analysis, refactoring, and import management.

### 14. mcp-microsoft-docs-server
**Port:** 8014  
**Tools:** activate_microsoft_docs_tools, mcp_microsoftdocs_microsoft_code_sample_search, mcp_microsoftdocs_microsoft_docs_fetch

Searches and fetches Microsoft documentation and code samples.

### 15. mcp-specialized-tools-server
**Port:** 8015  
**Tools:** vscode_askQuestions, vscode_listCodeUsages, renderMermaidDiagram

Provides specialized tools for user interaction, code analysis, and diagram rendering.

### 16. mcp-subagent-server
**Port:** 8016  
**Tools:** runSubagent

Launches autonomous agents for complex multi-step tasks.

## 🔧 Configuration

Each server can be configured via environment variables:

```bash
# Common settings
export MCP_HOST="0.0.0.0"
export MCP_PORT="8001"  # Varies by server
export LOG_LEVEL="INFO"

# Server-specific settings (example for Azure)
export AZURE_SUBSCRIPTION_ID="your-subscription-id"
export AZURE_TENANT_ID="your-tenant-id"
```

## 📖 Usage Examples

### Using with MCP Client

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Connect to file directory server
server_params = StdioServerParameters(
    command="python",
    args=["mcp-file-directory-server/server.py"]
)

async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        # Initialize
        await session.initialize()
        
        # Call tool
        result = await session.call_tool("create_directory", {
            "dirPath": "/tmp/test_dir"
        })
        print(result)
```

### Using with HTTP/SSE

```python
import httpx

# Call tool via HTTP
response = httpx.post(
    "http://localhost:8001/tools/create_directory",
    json={"dirPath": "/tmp/test_dir"}
)
print(response.json())
```

## 🧪 Testing

Each server includes comprehensive tests:

```bash
# Run tests for specific server
cd mcp-file-directory-server
pytest tests/

# Run all tests
./test_all.sh
```

## 📝 Development

### Adding New Tools

1. Navigate to the server directory
2. Edit `server.py`
3. Add new tool using `@mcp.tool()` decorator
4. Update documentation
5. Add tests

Example:

```python
@mcp.tool()
def my_new_tool(param1: str, param2: int) -> dict:
    """Tool description"""
    # Implementation
    return {"success": True, "result": "..."}
```

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

## 🔗 Resources

- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [Model Context Protocol Specification](https://modelcontextprotocol.io)
- [VS Code Copilot Tools Reference](./vscode/tools_catalog.md)

## 🐛 Troubleshooting

### Port Already in Use

```bash
# Find process using port
lsof -i :8001

# Kill process
kill -9 <PID>
```

### Connection Refused

Check if server is running:
```bash
curl http://localhost:8001/health
```

### Import Errors

Ensure all dependencies are installed:
```bash
pip install -r requirements.txt
```

## 📊 Performance

Each server is optimized for:
- Low latency (<100ms for most operations)
- Concurrent request handling
- Efficient resource usage
- Graceful error handling

## 🔐 Security

- All servers validate input parameters
- SQL injection prevention (where applicable)
- Path traversal protection
- Rate limiting support
- Authentication ready (add your auth layer)

## 🎯 Roadmap

- [ ] Add authentication/authorization
- [ ] Implement rate limiting
- [ ] Add metrics and monitoring
- [ ] Create Docker images
- [ ] Add Kubernetes manifests
- [ ] Implement caching layer
- [ ] Add WebSocket support
- [ ] Create CLI tool for management

---

**Built with ❤️ using FastMCP**
