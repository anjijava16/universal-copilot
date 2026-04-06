"""
Script to generate all 16 MCP server projects with their complete structure.
"""

import os
from pathlib import Path

# Server configurations
SERVERS = [
    {
        "id": "01",
        "name": "mcp-file-directory-server",
        "title": "File & Directory Management Server",
        "port": 8001,
        "emoji": "📂",
        "tools": [
            ("create_directory", "dirPath: str", "Create directory structure recursively"),
            ("create_file", "filePath: str, content: str", "Create new file with content"),
            ("list_dir", "path: str", "List directory contents"),
            ("file_search", "query: str, maxResults: Optional[int] = None", "Search files by glob pattern"),
            ("grep_search", "query: str, isRegexp: bool, includePattern: Optional[str] = None, maxResults: Optional[int] = None, includeIgnoredFiles: bool = False", "Search file contents by text/regex"),
        ]
    },
    {
        "id": "02",
        "name": "mcp-file-operations-server",
        "title": "File Operations Server",
        "port": 8002,
        "emoji": "📝",
        "tools": [
            ("read_file", "filePath: str, startLine: int, endLine: int", "Read file contents with line range"),
            ("replace_string_in_file", "filePath: str, oldString: str, newString: str", "Replace text in file"),
            ("multi_replace_string_in_file", "explanation: str, replacements: List[Dict]", "Multiple replacements in one call"),
            ("view_image", "filePath: str", "View image file contents"),
            ("get_changed_files", "repositoryPath: Optional[str] = None, sourceControlState: Optional[List[str]] = None", "Get git diffs"),
            ("get_errors", "filePaths: Optional[List[str]] = None", "Get compile/lint errors"),
        ]
    },
    {
        "id": "03",
        "name": "mcp-search-discovery-server",
        "title": "Search & Discovery Server",
        "port": 8003,
        "emoji": "🔍",
        "tools": [
            ("semantic_search", "query: str", "Natural language code search"),
            ("get_search_view_results", "", "Get search view results"),
            ("github_repo", "repo: str, query: str", "Search GitHub repository"),
            ("fetch_webpage", "urls: List[str], query: str", "Fetch webpage content"),
        ]
    },
    {
        "id": "04",
        "name": "mcp-notebook-operations-server",
        "title": "Notebook Operations Server",
        "port": 8004,
        "emoji": "📓",
        "tools": [
            ("create_new_jupyter_notebook", "query: str", "Generate new Jupyter notebook"),
            ("edit_notebook_file", "filePath: str, cellId: str, editType: str, newCode: Optional[str] = None, language: Optional[str] = None", "Edit notebook cells"),
            ("copilot_getNotebookSummary", "filePath: str", "Get notebook cell summary"),
            ("run_notebook_cell", "filePath: str, cellId: str, reason: Optional[str] = None, continueOnError: bool = False", "Run notebook cell"),
            ("read_notebook_cell_output", "filePath: str, cellId: str", "Read cell output"),
        ]
    },
    {
        "id": "05",
        "name": "mcp-vscode-integration-server",
        "title": "VS Code Integration Server",
        "port": 8005,
        "emoji": "🔧",
        "tools": [
            ("create_new_workspace", "query: str", "Create complete project structure"),
            ("get_project_setup_info", "projectType: str", "Get project setup information"),
            ("get_vscode_api", "query: str", "Get VS Code API documentation"),
            ("install_extension", "id: str, name: str", "Install VS Code extension"),
            ("run_vscode_command", "commandId: str, name: str, args: Optional[List[str]] = None, skipCheck: bool = False", "Run VS Code command"),
            ("vscode_searchExtensions_internal", "category: Optional[str] = None, keywords: Optional[List[str]] = None, ids: Optional[List[str]] = None", "Search VS Code extensions"),
        ]
    },
    {
        "id": "06",
        "name": "mcp-terminal-process-server",
        "title": "Terminal & Process Management Server",
        "port": 8006,
        "emoji": "💻",
        "tools": [
            ("run_in_terminal", "command: str, explanation: str, goal: str, isBackground: bool, timeout: int", "Execute shell command"),
            ("await_terminal", "id: str, timeout: int", "Wait for background command"),
            ("get_terminal_output", "id: str", "Get terminal output"),
            ("kill_terminal", "id: str", "Kill terminal process"),
            ("terminal_last_command", "", "Get last command"),
            ("terminal_selection", "", "Get terminal selection"),
        ]
    },
    {
        "id": "07",
        "name": "mcp-memory-management-server",
        "title": "Memory Management Server",
        "port": 8007,
        "emoji": "🧠",
        "tools": [
            ("memory", "command: str, path: Optional[str] = None, file_text: Optional[str] = None, old_str: Optional[str] = None, new_str: Optional[str] = None", "Manage persistent memory"),
            ("resolve_memory_file_uri", "path: str", "Resolve memory file URI"),
        ]
    },
    {
        "id": "08",
        "name": "mcp-task-todo-server",
        "title": "Task & Todo Management Server",
        "port": 8008,
        "emoji": "✅",
        "tools": [
            ("manage_todo_list", "todoList: List[Dict]", "Manage structured todo list"),
            ("create_and_run_task", "workspaceFolder: str, task: Dict", "Create and run VS Code task"),
        ]
    },
    {
        "id": "09",
        "name": "mcp-azure-auth-server",
        "title": "Azure Authentication & Resources Server",
        "port": 8009,
        "emoji": "☁️",
        "tools": [
            ("activate_azure_authentication_and_resource_management", "", "Activate Azure auth tools"),
            ("azureResources_getAzureActivityLog", "", "Get Azure activity log"),
            ("activate_azure_subscription_and_resource_group_tools", "", "Activate subscription tools"),
        ]
    },
    {
        "id": "10",
        "name": "mcp-azure-services-server",
        "title": "Azure Services Server",
        "port": 8010,
        "emoji": "🌐",
        "tools": [
            ("azure_bicep_get_azure_verified_module", "resourceType: str", "Get Bicep module"),
            ("mcp_azure_mcp_applens", "intent: str, command: Optional[str] = None, parameters: Optional[Dict] = None, learn: bool = False", "AppLens diagnostics"),
            ("mcp_azure_mcp_azureterraformbestpractices", "intent: str, command: Optional[str] = None, parameters: Optional[Dict] = None, learn: bool = False", "Terraform best practices"),
            ("mcp_azure_mcp_confidentialledger", "intent: str, command: Optional[str] = None, parameters: Optional[Dict] = None, learn: bool = False", "Confidential Ledger operations"),
            ("mcp_azure_mcp_resourcehealth", "intent: str, command: Optional[str] = None, parameters: Optional[Dict] = None, learn: bool = False", "Resource health monitoring"),
            ("mcp_azure_mcp_speech", "intent: str, command: Optional[str] = None, parameters: Optional[Dict] = None, learn: bool = False", "Azure AI Speech operations"),
        ]
    },
    {
        "id": "11",
        "name": "mcp-azure-cli-server",
        "title": "Azure CLI & Templates Server",
        "port": 8011,
        "emoji": "⚙️",
        "tools": [
            ("activate_azure_cli_tools", "", "Activate Azure CLI tools"),
            ("activate_dotnet_project_template_management", "", "Activate .NET template tools"),
        ]
    },
    {
        "id": "12",
        "name": "mcp-python-env-server",
        "title": "Python Environment Management Server",
        "port": 8012,
        "emoji": "🐍",
        "tools": [
            ("configure_python_environment", "resourcePath: Optional[str] = None", "Configure Python environment"),
            ("install_python_packages", "packageList: List[str], resourcePath: Optional[str] = None", "Install Python packages"),
            ("activate_python_environment_tools", "", "Activate environment tools"),
            ("configure_notebook", "filePath: str", "Configure notebook"),
            ("activate_notebook_kernel_configuration", "", "Activate kernel configuration"),
            ("activate_notebook_package_management", "", "Activate package management"),
        ]
    },
    {
        "id": "13",
        "name": "mcp-python-analysis-server",
        "title": "Python Analysis & Refactoring Server",
        "port": 8013,
        "emoji": "🔬",
        "tools": [
            ("activate_python_syntax_validation_tools", "", "Activate syntax validation"),
            ("activate_python_import_analysis_tools", "", "Activate import analysis"),
            ("mcp_pylance_mcp_s_pylanceDocString", "fileUri: str, symbolName: str", "Get Python docstring"),
            ("mcp_pylance_mcp_s_pylanceInvokeRefactoring", "fileUri: str, name: str, mode: Optional[str] = 'update'", "Apply code refactoring"),
            ("mcp_pylance_mcp_s_pylanceImports", "workspaceRoot: str", "Analyze imports"),
        ]
    },
    {
        "id": "14",
        "name": "mcp-microsoft-docs-server",
        "title": "Microsoft Documentation Server",
        "port": 8014,
        "emoji": "📚",
        "tools": [
            ("activate_microsoft_docs_tools", "", "Activate docs tools"),
            ("mcp_microsoftdocs_microsoft_code_sample_search", "query: str, language: Optional[str] = None", "Search code samples"),
            ("mcp_microsoftdocs_microsoft_docs_fetch", "url: str", "Fetch documentation page"),
        ]
    },
    {
        "id": "15",
        "name": "mcp-specialized-tools-server",
        "title": "Specialized Tools Server",
        "port": 8015,
        "emoji": "🛠️",
        "tools": [
            ("vscode_askQuestions", "questions: List[Dict]", "Ask user questions"),
            ("vscode_listCodeUsages", "symbol: str, lineContent: str, uri: Optional[str] = None, filePath: Optional[str] = None", "Find code symbol usages"),
            ("renderMermaidDiagram", "markup: Optional[str] = None, title: Optional[str] = None", "Render Mermaid diagram"),
        ]
    },
    {
        "id": "16",
        "name": "mcp-subagent-server",
        "title": "Subagent Server",
        "port": 8016,
        "emoji": "🤖",
        "tools": [
            ("runSubagent", "prompt: str, description: str, agentName: Optional[str] = None", "Launch autonomous agent"),
        ]
    },
]


def generate_server_py(server):
    """Generate server.py file"""
    tools_code = []
    
    for tool_name, params, description in server["tools"]:
        # Generate tool function
        tool_code = f'''
@mcp.tool()
def {tool_name}({params}) -> Dict[str, Any]:
    """
    {description}
    
    Returns:
        Success status and result data
    """
    try:
        # TODO: Implement {tool_name} logic
        logger.info(f"Executing {tool_name}")
        
        return {{
            "success": True,
            "message": "{tool_name} executed successfully",
            "data": {{}}
        }}
    except Exception as e:
        logger.error(f"Error in {tool_name}: {{str(e)}}")
        return {{
            "success": False,
            "error": str(e)
        }}
'''
        tools_code.append(tool_code)
    
    return f'''"""
{server["title"]}
Port: {server["port"]}
"""

import os
import asyncio
import logging
from typing import List, Optional, Dict, Any
from fastmcp import FastMCP

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP(
    "{server["title"]}",
    port=int(os.getenv("PORT", "{server["port"]}"))
)

{"".join(tools_code)}

@mcp.resource("doc://api")
def get_api_docs() -> str:
    """API documentation for {server["title"]}"""
    return """
    # {server["title"]} API
    
    ## Tools
    
{chr(10).join(f"    {i+1}. {tool[0]} - {tool[2]}" for i, tool in enumerate(server["tools"]))}
    """


async def main():
    """Start the MCP server"""
    logger.info("{server['emoji']} Starting {server['title']}...")
    logger.info(f"📡 Port: {server['port']}")
    
    await mcp.run_async(
        transport="sse",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "{server['port']}"))
    )


if __name__ == "__main__":
    asyncio.run(main())
'''


def generate_readme(server):
    """Generate README.md file"""
    tools_docs = []
    for i, (tool_name, params, description) in enumerate(server["tools"], 1):
        tools_docs.append(f'''
### {i}. {tool_name}

{description}

```python
await client.call_tool("{tool_name}", {{
    # Add parameters here
}})
```
''')
    
    return f'''# {server["title"]} {server["emoji"]}

Port: {server["port"]}

## Features

{chr(10).join(f"- **{tool[0]}**: {tool[2]}" for tool in server["tools"])}

## Installation

```bash
pip install -r requirements.txt
```

## Running the Server

```bash
# Default port {server["port"]}
python server.py

# Custom port
PORT=9000 python server.py
```

## Tools

{"".join(tools_docs)}

## Configuration

Environment variables:

- `PORT`: Server port (default: {server["port"]})
- `LOG_LEVEL`: Logging level (default: INFO)

## License

MIT
'''


def generate_requirements():
    """Generate requirements.txt"""
    return """fastmcp>=0.1.0
mcp>=0.1.0
"""


def main():
    """Generate all server projects"""
    base_dir = Path("mcp_servers")
    
    for server in SERVERS:
        server_dir = base_dir / f"{server['id']}-{server['name']}"
        server_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate server.py
        (server_dir / "server.py").write_text(generate_server_py(server))
        
        # Generate README.md
        (server_dir / "README.md").write_text(generate_readme(server))
        
        # Generate requirements.txt
        (server_dir / "requirements.txt").write_text(generate_requirements())
        
        print(f"✅ Generated {server['name']}")
    
    print(f"\n🎉 Successfully generated all {len(SERVERS)} MCP servers!")


if __name__ == "__main__":
    main()
