# MCP Servers Collection - Complete Index

## 📑 Documentation Index

### Getting Started
- [README.md](./README.md) - Main project documentation
- [QUICKSTART.md](./QUICKSTART.md) - 5-minute setup guide
- [PROJECT_SUMMARY.md](./PROJECT_SUMMARY.md) - Project overview and statistics
- [ARCHITECTURE.md](./ARCHITECTURE.md) - System architecture and design

### Configuration
- [.env.example](./.env.example) - Environment variables template
- [docker-compose.yml](./docker-compose.yml) - Docker orchestration
- [Dockerfile](./Dockerfile) - Container image definition

### Scripts
- [install_all.sh](./install_all.sh) - Install all servers
- [run_all.sh](./run_all.sh) - Run all servers
- [test_all.sh](./test_all.sh) - Test all servers
- [generate_all_servers.py](./generate_all_servers.py) - Server generator

### Examples
- [client_example.py](./client_example.py) - Python client usage examples

## 🖥️ Server Index

### 1. File & Directory Management Server (Port 8001)
**Location**: `01-mcp-file-directory-server/`
- [server.py](./mcp_servers/01-mcp-file-directory-server/server.py)
- [README.md](./mcp_servers/01-mcp-file-directory-server/README.md)
- [requirements.txt](./mcp_servers/01-mcp-file-directory-server/requirements.txt)

**Tools** (5):
1. `create_directory` - Create directory structure recursively
2. `create_file` - Create new file with content
3. `list_dir` - List directory contents
4. `file_search` - Search files by glob pattern
5. `grep_search` - Search file contents by text/regex

---

### 2. File Operations Server (Port 8002)
**Location**: `02-mcp-file-operations-server/`
- [server.py](./mcp_servers/02-mcp-file-operations-server/server.py)
- [README.md](./mcp_servers/02-mcp-file-operations-server/README.md)
- [requirements.txt](./mcp_servers/02-mcp-file-operations-server/requirements.txt)

**Tools** (6):
1. `read_file` - Read file contents with line range
2. `replace_string_in_file` - Replace text in file
3. `multi_replace_string_in_file` - Multiple replacements in one call
4. `view_image` - View image file contents
5. `get_changed_files` - Get git diffs
6. `get_errors` - Get compile/lint errors

---

### 3. Search & Discovery Server (Port 8003)
**Location**: `03-mcp-search-discovery-server/`
- [server.py](./mcp_servers/03-mcp-search-discovery-server/server.py)
- [README.md](./mcp_servers/03-mcp-search-discovery-server/README.md)
- [requirements.txt](./mcp_servers/03-mcp-search-discovery-server/requirements.txt)

**Tools** (4):
1. `semantic_search` - Natural language code search
2. `get_search_view_results` - Get search view results
3. `github_repo` - Search GitHub repository
4. `fetch_webpage` - Fetch webpage content

---

### 4. Notebook Operations Server (Port 8004)
**Location**: `04-mcp-notebook-operations-server/`
- [server.py](./mcp_servers/04-mcp-notebook-operations-server/server.py)
- [README.md](./mcp_servers/04-mcp-notebook-operations-server/README.md)
- [requirements.txt](./mcp_servers/04-mcp-notebook-operations-server/requirements.txt)

**Tools** (5):
1. `create_new_jupyter_notebook` - Generate new Jupyter notebook
2. `edit_notebook_file` - Edit notebook cells
3. `copilot_getNotebookSummary` - Get notebook cell summary
4. `run_notebook_cell` - Run notebook cell
5. `read_notebook_cell_output` - Read cell output

---

### 5. VS Code Integration Server (Port 8005)
**Location**: `05-mcp-vscode-integration-server/`
- [server.py](./mcp_servers/05-mcp-vscode-integration-server/server.py)
- [README.md](./mcp_servers/05-mcp-vscode-integration-server/README.md)
- [requirements.txt](./mcp_servers/05-mcp-vscode-integration-server/requirements.txt)

**Tools** (6):
1. `create_new_workspace` - Create complete project structure
2. `get_project_setup_info` - Get project setup information
3. `get_vscode_api` - Get VS Code API documentation
4. `install_extension` - Install VS Code extension
5. `run_vscode_command` - Run VS Code command
6. `vscode_searchExtensions_internal` - Search VS Code extensions

---

### 6. Terminal & Process Management Server (Port 8006)
**Location**: `06-mcp-terminal-process-server/`
- [server.py](./mcp_servers/06-mcp-terminal-process-server/server.py)
- [README.md](./mcp_servers/06-mcp-terminal-process-server/README.md)
- [requirements.txt](./mcp_servers/06-mcp-terminal-process-server/requirements.txt)

**Tools** (6):
1. `run_in_terminal` - Execute shell command
2. `await_terminal` - Wait for background command
3. `get_terminal_output` - Get terminal output
4. `kill_terminal` - Kill terminal process
5. `terminal_last_command` - Get last command
6. `terminal_selection` - Get terminal selection

---

### 7. Memory Management Server (Port 8007)
**Location**: `07-mcp-memory-management-server/`
- [server.py](./mcp_servers/07-mcp-memory-management-server/server.py)
- [README.md](./mcp_servers/07-mcp-memory-management-server/README.md)
- [requirements.txt](./mcp_servers/07-mcp-memory-management-server/requirements.txt)

**Tools** (2):
1. `memory` - Manage persistent memory (view, create, str_replace, insert, delete, rename)
2. `resolve_memory_file_uri` - Resolve memory file URI

---

### 8. Task & Todo Management Server (Port 8008)
**Location**: `08-mcp-task-todo-server/`
- [server.py](./mcp_servers/08-mcp-task-todo-server/server.py)
- [README.md](./mcp_servers/08-mcp-task-todo-server/README.md)
- [requirements.txt](./mcp_servers/08-mcp-task-todo-server/requirements.txt)

**Tools** (2):
1. `manage_todo_list` - Manage structured todo list
2. `create_and_run_task` - Create and run VS Code task

---

### 9. Azure Authentication & Resources Server (Port 8009)
**Location**: `09-mcp-azure-auth-server/`
- [server.py](./mcp_servers/09-mcp-azure-auth-server/server.py)
- [README.md](./mcp_servers/09-mcp-azure-auth-server/README.md)
- [requirements.txt](./mcp_servers/09-mcp-azure-auth-server/requirements.txt)

**Tools** (3):
1. `activate_azure_authentication_and_resource_management` - Activate Azure auth tools
2. `azureResources_getAzureActivityLog` - Get Azure activity log
3. `activate_azure_subscription_and_resource_group_tools` - Activate subscription tools

---

### 10. Azure Services Server (Port 8010)
**Location**: `10-mcp-azure-services-server/`
- [server.py](./mcp_servers/10-mcp-azure-services-server/server.py)
- [README.md](./mcp_servers/10-mcp-azure-services-server/README.md)
- [requirements.txt](./mcp_servers/10-mcp-azure-services-server/requirements.txt)

**Tools** (6):
1. `azure_bicep_get_azure_verified_module` - Get Bicep module
2. `mcp_azure_mcp_applens` - AppLens diagnostics
3. `mcp_azure_mcp_azureterraformbestpractices` - Terraform best practices
4. `mcp_azure_mcp_confidentialledger` - Confidential Ledger operations
5. `mcp_azure_mcp_resourcehealth` - Resource health monitoring
6. `mcp_azure_mcp_speech` - Azure AI Speech operations

---

### 11. Azure CLI & Templates Server (Port 8011)
**Location**: `11-mcp-azure-cli-server/`
- [server.py](./mcp_servers/11-mcp-azure-cli-server/server.py)
- [README.md](./mcp_servers/11-mcp-azure-cli-server/README.md)
- [requirements.txt](./mcp_servers/11-mcp-azure-cli-server/requirements.txt)

**Tools** (2):
1. `activate_azure_cli_tools` - Activate Azure CLI tools
2. `activate_dotnet_project_template_management` - Activate .NET template tools

---

### 12. Python Environment Management Server (Port 8012)
**Location**: `12-mcp-python-env-server/`
- [server.py](./mcp_servers/12-mcp-python-env-server/server.py)
- [README.md](./mcp_servers/12-mcp-python-env-server/README.md)
- [requirements.txt](./mcp_servers/12-mcp-python-env-server/requirements.txt)

**Tools** (6):
1. `configure_python_environment` - Configure Python environment
2. `install_python_packages` - Install Python packages
3. `activate_python_environment_tools` - Activate environment tools
4. `configure_notebook` - Configure notebook
5. `activate_notebook_kernel_configuration` - Activate kernel configuration
6. `activate_notebook_package_management` - Activate package management

---

### 13. Python Analysis & Refactoring Server (Port 8013)
**Location**: `13-mcp-python-analysis-server/`
- [server.py](./mcp_servers/13-mcp-python-analysis-server/server.py)
- [README.md](./mcp_servers/13-mcp-python-analysis-server/README.md)
- [requirements.txt](./mcp_servers/13-mcp-python-analysis-server/requirements.txt)

**Tools** (5):
1. `activate_python_syntax_validation_tools` - Activate syntax validation
2. `activate_python_import_analysis_tools` - Activate import analysis
3. `mcp_pylance_mcp_s_pylanceDocString` - Get Python docstring
4. `mcp_pylance_mcp_s_pylanceInvokeRefactoring` - Apply code refactoring
5. `mcp_pylance_mcp_s_pylanceImports` - Analyze imports

---

### 14. Microsoft Documentation Server (Port 8014)
**Location**: `14-mcp-microsoft-docs-server/`
- [server.py](./mcp_servers/14-mcp-microsoft-docs-server/server.py)
- [README.md](./mcp_servers/14-mcp-microsoft-docs-server/README.md)
- [requirements.txt](./mcp_servers/14-mcp-microsoft-docs-server/requirements.txt)

**Tools** (3):
1. `activate_microsoft_docs_tools` - Activate docs tools
2. `mcp_microsoftdocs_microsoft_code_sample_search` - Search code samples
3. `mcp_microsoftdocs_microsoft_docs_fetch` - Fetch documentation page

---

### 15. Specialized Tools Server (Port 8015)
**Location**: `15-mcp-specialized-tools-server/`
- [server.py](./mcp_servers/15-mcp-specialized-tools-server/server.py)
- [README.md](./mcp_servers/15-mcp-specialized-tools-server/README.md)
- [requirements.txt](./mcp_servers/15-mcp-specialized-tools-server/requirements.txt)

**Tools** (3):
1. `vscode_askQuestions` - Ask user questions
2. `vscode_listCodeUsages` - Find code symbol usages
3. `renderMermaidDiagram` - Render Mermaid diagram

---

### 16. Subagent Server (Port 8016)
**Location**: `16-mcp-subagent-server/`
- [server.py](./mcp_servers/16-mcp-subagent-server/server.py)
- [README.md](./mcp_servers/16-mcp-subagent-server/README.md)
- [requirements.txt](./mcp_servers/16-mcp-subagent-server/requirements.txt)

**Tools** (1):
1. `runSubagent` - Launch autonomous agent

---

## 📊 Statistics Summary

| Metric | Value |
|--------|-------|
| Total Servers | 16 |
| Total Tools | 76 |
| Total Files | 60+ |
| Documentation Pages | 20+ |
| Code Files | 16 server.py |
| Configuration Files | 16 requirements.txt |
| Shell Scripts | 3 |
| Docker Files | 2 |

## 🔗 Quick Links

### Documentation
- [Main README](./README.md)
- [Quick Start](./QUICKSTART.md)
- [Architecture](./ARCHITECTURE.md)
- [Project Summary](./PROJECT_SUMMARY.md)

### Tools Reference
- [VS Code Tools Catalog](../vscode/tools_catalog.md)

### External Resources
- [FastMCP GitHub](https://github.com/jlowin/fastmcp)
- [MCP Specification](https://modelcontextprotocol.io)
- [VS Code API](https://code.visualstudio.com/api)

---

**Last Updated**: 2024-04-05  
**Version**: 1.0.0
