# VS Code Copilot Tools Catalog

**Total Tools: 76**

This document catalogs all 76 tools available in the VS Code Copilot panel/editAgent interface, extracted from the request log.

---

## Table of Contents

1. [File & Directory Management](#file--directory-management) (5 tools)
2. [File Operations](#file-operations) (6 tools)
3. [Search & Discovery](#search--discovery) (4 tools)
4. [Notebook Operations](#notebook-operations) (5 tools)
5. [VS Code Integration](#vs-code-integration) (6 tools)
6. [Terminal & Process Management](#terminal--process-management) (6 tools)
7. [Memory Management](#memory-management) (2 tools)
8. [Task & Todo Management](#task--todo-management) (2 tools)
9. [Azure Authentication & Resources](#azure-authentication--resources) (3 tools)
10. [Azure Services](#azure-services) (6 tools)
11. [Azure CLI & Templates](#azure-cli--templates) (2 tools)
12. [Python Environment Management](#python-environment-management) (6 tools)
13. [Python Analysis & Refactoring](#python-analysis--refactoring) (5 tools)
14. [Microsoft Documentation](#microsoft-documentation) (3 tools)
15. [Specialized Tools](#specialized-tools) (3 tools)
16. [Subagent](#subagent) (1 tool)

---

## File & Directory Management

### 1. create_directory
**Description:** Create a new directory structure in the workspace. Will recursively create all directories in the path, like mkdir -p.

**Parameters:**
- `dirPath` (string, required): The absolute path to the directory to create.

---

### 2. create_file
**Description:** Create a new file in the workspace with specified content. The directory will be created if it does not already exist.

**Parameters:**
- `filePath` (string, required): The absolute path to the file to create.
- `content` (string, required): The content to write to the file.

---

### 3. list_dir
**Description:** List the contents of a directory. Result will have the name of the child. If the name ends in /, it's a folder, otherwise a file.

**Parameters:**
- `path` (string, required): The absolute path to the directory to list.

---

### 4. file_search
**Description:** Search for files in the workspace by glob pattern. Returns only the paths of matching files.

**Parameters:**
- `query` (string, required): Glob pattern to match files.
- `maxResults` (number, optional): Maximum number of results to return.

**Examples:**
- `**/*.{js,ts}` - all js/ts files
- `src/**` - all files under src folder
- `**/foo/**/*.js` - all js files under any foo folder

---

### 5. grep_search
**Description:** Fast text search in the workspace using exact string or regex patterns.

**Parameters:**
- `query` (string, required): Pattern to search for (supports regex).
- `isRegexp` (boolean, required): Whether the pattern is a regex.
- `includePattern` (string, optional): Glob pattern to filter files.
- `maxResults` (number, optional): Maximum results to return.
- `includeIgnoredFiles` (boolean, optional): Include .gitignore files.

---

## File Operations

### 6. read_file
**Description:** Read the contents of a file with line range specification.

**Parameters:**
- `filePath` (string, required): Absolute path of the file.
- `startLine` (number, required): Starting line number (1-based).
- `endLine` (number, required): Ending line number (1-based).

---

### 7. replace_string_in_file
**Description:** Make edits in an existing file by replacing exact text matches.

**Parameters:**
- `filePath` (string, required): Absolute path to the file.
- `oldString` (string, required): Exact literal text to replace (must be unique).
- `newString` (string, required): Replacement text.

**Critical:** Include 3+ lines of context before and after the target text.

---

### 8. multi_replace_string_in_file
**Description:** Apply multiple replace operations in a single call (more efficient than sequential calls).

**Parameters:**
- `explanation` (string, required): Brief explanation of the operation.
- `replacements` (array, required): Array of replacement operations, each with:
  - `filePath` (string)
  - `oldString` (string)
  - `newString` (string)

---

### 9. view_image
**Description:** View the contents of an image file (png, jpg, jpeg, gif, webp).

**Parameters:**
- `filePath` (string, required): Absolute path of the image file.

---

### 10. get_changed_files
**Description:** Get git diffs of current file changes in a git repository.

**Parameters:**
- `repositoryPath` (string, optional): Absolute path to git repository.
- `sourceControlState` (array, optional): Filter by state: `staged`, `unstaged`, `merge-conflicts`.

---

### 11. get_errors
**Description:** Get compile or lint errors in specific files or across all files.

**Parameters:**
- `filePaths` (array, optional): Absolute paths to files/folders. Omit to get all errors.

---

## Search & Discovery

### 12. semantic_search
**Description:** Natural language search for relevant code or documentation in the workspace.

**Parameters:**
- `query` (string, required): Natural language query describing what to find.

---

### 13. get_search_view_results
**Description:** Get the results from the search view.

**Parameters:** None

---

### 14. github_repo
**Description:** Search a GitHub repository for relevant source code snippets.

**Parameters:**
- `repo` (string, required): Repository name in format `<owner>/<repo>`.
- `query` (string, required): Search query.

---

### 15. fetch_webpage
**Description:** Fetch the main content from a web page for summarizing or analyzing.

**Parameters:**
- `urls` (array, required): Array of URLs to fetch.
- `query` (string, required): Query to search for in the content.

---

## Notebook Operations

### 16. create_new_jupyter_notebook
**Description:** Generate a new Jupyter Notebook (.ipynb) in VS Code.

**Parameters:**
- `query` (string, required): Description of the notebook to create.

---

### 17. edit_notebook_file
**Description:** Edit an existing Notebook file (insert, delete, or edit cells).

**Parameters:**
- `filePath` (string, required): Absolute path to notebook file.
- `cellId` (string, required): Cell ID or `TOP`/`BOTTOM`.
- `newCode` (string/array, optional): Code for the cell.
- `language` (string, optional): Cell language (markdown, python, etc.).
- `editType` (string, required): Operation type: `insert`, `delete`, or `edit`.

---

### 18. copilot_getNotebookSummary
**Description:** Get list of notebook cells with IDs, types, line ranges, and execution info.

**Parameters:**
- `filePath` (string, required): Absolute path to notebook file.

---

### 19. run_notebook_cell
**Description:** Run a code cell in a notebook file directly in the editor.

**Parameters:**
- `filePath` (string, required): Absolute path to notebook file.
- `cellId` (string, required): ID of the code cell to execute.
- `reason` (string, optional): Explanation of why the cell is being run.
- `continueOnError` (boolean, optional): Continue execution if error occurs.

---

### 20. read_notebook_cell_output
**Description:** Retrieve output for a notebook cell from its most recent execution.

**Parameters:**
- `filePath` (string, required): Absolute path to notebook file.
- `cellId` (string, required): ID of the cell.

---

## VS Code Integration

### 21. create_new_workspace
**Description:** Get comprehensive setup steps for creating complete project structures (full project initialization, not individual files).

**Parameters:**
- `query` (string, required): Description of the workspace to create.

**Use for:** TypeScript projects, React apps, MCP servers, VS Code extensions, Next.js, Vite projects.

---

### 22. get_project_setup_info
**Description:** Get project setup information for a VS Code workspace based on project type.

**Parameters:**
- `projectType` (string, required): Type of project. Supported values:
  - `python-script`, `python-project`
  - `mcp-server`, `model-context-protocol-server`
  - `vscode-extension`
  - `next-js`, `vite`
  - `other`

---

### 23. get_vscode_api
**Description:** Get comprehensive VS Code API documentation for extension development.

**Parameters:**
- `query` (string, required): Query for VS Code API documentation.

**Use for:** Extension development, API references, contribution points, proposed APIs.

---

### 24. install_extension
**Description:** Install an extension in VS Code (for workspace creation only).

**Parameters:**
- `id` (string, required): Extension ID in format `<publisher>.<extension>`.
- `name` (string, required): Extension name.

---

### 25. run_vscode_command
**Description:** Run a command in VS Code (for workspace creation only).

**Parameters:**
- `commandId` (string, required): Command ID.
- `name` (string, required): Command name.
- `args` (array, optional): Command arguments.
- `skipCheck` (boolean, optional): Skip existence check.

---

### 26. vscode_searchExtensions_internal
**Description:** Browse Visual Studio Code Extensions Marketplace.

**Parameters:**
- `category` (string, optional): Extension category (AI, Azure, Data Science, etc.).
- `keywords` (array, optional): Search keywords.
- `ids` (array, optional): Extension IDs.

---

## Terminal & Process Management

### 27. run_in_terminal
**Description:** Execute shell commands in a persistent zsh terminal session.

**Parameters:**
- `command` (string, required): Command to run.
- `explanation` (string, required): One-sentence description.
- `goal` (string, required): Short goal description.
- `isBackground` (boolean, required): Whether command runs in background.
- `timeout` (number, required): Timeout in milliseconds (0 for no timeout).

---

### 28. await_terminal
**Description:** Wait for a background terminal command to complete.

**Parameters:**
- `id` (string, required): Terminal ID from run_in_terminal.
- `timeout` (number, required): Timeout in milliseconds.

---

### 29. get_terminal_output
**Description:** Get output of a terminal command previously started.

**Parameters:**
- `id` (string, required): Terminal ID.

---

### 30. kill_terminal
**Description:** Kill a terminal by its ID.

**Parameters:**
- `id` (string, required): Terminal ID to kill.

---

### 31. terminal_last_command
**Description:** Get the last command run in the active terminal.

**Parameters:** None

---

### 32. terminal_selection
**Description:** Get the current selection in the active terminal.

**Parameters:** None

---

## Memory Management

### 33. memory
**Description:** Manage persistent memory system with three scopes: user, session, and repository.

**Commands:**
- `view`: View file/directory contents
- `create`: Create new file
- `str_replace`: Replace exact string
- `insert`: Insert text at line number
- `delete`: Delete file/directory
- `rename`: Rename/move file/directory

**Parameters:**
- `command` (string, required): Operation to perform.
- `path` (string): Path inside /memories/.
- `file_text` (string): Content for create.
- `old_str`, `new_str` (string): For str_replace.
- `insert_line` (number), `insert_text` (string): For insert.
- `view_range` (array): Line range for view.
- `old_path`, `new_path` (string): For rename.

**Memory Scopes:**
- `/memories/` - User memory (persistent across all workspaces)
- `/memories/session/` - Session memory (current conversation only)
- `/memories/repo/` - Repository memory (workspace-scoped)

---

### 34. resolve_memory_file_uri
**Description:** Resolve a memory file path to its fully qualified URI.

**Parameters:**
- `path` (string, required): Memory file path (e.g., `/memories/session/plan.md`).

---

## Task & Todo Management

### 35. manage_todo_list
**Description:** Manage structured todo list to track progress throughout coding session.

**Parameters:**
- `todoList` (array, required): Complete array of all todo items, each with:
  - `id` (number): Unique identifier
  - `title` (string): Concise action-oriented label (3-7 words)
  - `status` (string): `not-started`, `in-progress`, or `completed`

**Use for:** Complex multi-step work, multiple tasks, planning and tracking.

---

### 36. create_and_run_task
**Description:** Create and run a build/run/custom task by generating tasks.json.

**Parameters:**
- `workspaceFolder` (string, required): Absolute path to workspace folder.
- `task` (object, required): Task configuration with:
  - `label` (string): Task label
  - `type` (string): Must be `shell`
  - `command` (string): Shell command
  - `args` (array, optional): Command arguments
  - `isBackground` (boolean, optional): Run in background
  - `problemMatcher` (array, optional): Problem matchers
  - `group` (string, optional): Task group

---

## Azure Authentication & Resources

### 37. activate_azure_authentication_and_resource_management
**Description:** Activate tools for managing Azure authentication contexts and querying Azure resources.

**Includes:**
- `azure_auth-get_auth_context`: Get current auth context
- `azure_auth-set_auth_context`: Modify auth context
- `azure_resources-query_azure_resource_graph`: Query Azure resources

**Parameters:** None

---

### 38. azureResources_getAzureActivityLog
**Description:** Get the Azure activity log.

**Parameters:** None

---

### 39. activate_azure_subscription_and_resource_group_tools
**Description:** Activate tools for managing Azure subscriptions and resource groups.

**Includes:**
- List resource groups within subscriptions
- List all/current subscriptions
- Get subscription IDs, names, states, tenant IDs

**Parameters:** None

---

## Azure Services

### 40. azure_bicep-get_azure_verified_module
**Description:** Get Bicep module code from Azure Verified Modules for a given resource type.

**Parameters:**
- `resourceType` (string, required): Full type name of the resource.

---

### 41. mcp_azure_mcp_applens
**Description:** AppLens diagnostic operations - Primary tool for diagnosing Azure resource issues.

**Parameters:**
- `intent` (string, required): Intent of the Azure operation.
- `command` (string, optional): Command to execute.
- `parameters` (object, optional): Parameters for the command.
- `learn` (boolean, optional): Discover available sub-commands.

**Use for:** Diagnosing issues, troubleshooting performance, investigating resource health, finding root causes.

---

### 42. mcp_azure_mcp_azureterraformbestpractices
**Description:** Get Terraform best practices for Azure.

**Parameters:** Same as mcp_azure_mcp_applens

---

### 43. mcp_azure_mcp_confidentialledger
**Description:** Azure Confidential Ledger operations for tamper-proof ledger entries.

**Parameters:** Same as mcp_azure_mcp_applens

---

### 44. mcp_azure_mcp_extension_azqr
**Description:** Run Azure Quick Review CLI (azqr) to generate compliance/security reports.

**Parameters:**
- `tenant` (string, optional): Microsoft Entra ID tenant ID/name
- `auth-method` (integer, optional): Authentication method
- `retry-delay`, `retry-max-delay`, `retry-max-retries` (number/integer, optional): Retry configuration
- `retry-mode` (integer, optional): Retry strategy
- `retry-network-timeout` (number, optional): Network timeout
- `subscription` (string, optional): Azure subscription ID/name
- `resource-group` (string, optional): Resource group name

---

### 45. mcp_azure_mcp_resourcehealth
**Description:** Monitor and diagnose Azure resource health status.

**Parameters:** Same as mcp_azure_mcp_applens

---

### 46. mcp_azure_mcp_speech
**Description:** Azure AI Services Speech operations (speech-to-text, audio processing, language detection).

**Parameters:** Same as mcp_azure_mcp_applens

---

### 47. mcp_azure_mcp_azd
**Description:** Azure Developer CLI (azd) for building, modernizing, and managing Azure applications.

**Parameters:** Same as mcp_azure_mcp_applens

---

### 48. mcp_azure_mcp_workbooks
**Description:** Manage Azure Workbooks resources and interactive data visualization dashboards.

**Parameters:** Same as mcp_azure_mcp_applens

---

### 49. mcp_azure_mcp_cloudarchitect
**Description:** Generate Azure architecture designs and recommendations.

**Parameters:** Same as mcp_azure_mcp_applens

---

### 50. mcp_azure_mcp_bicepschema
**Description:** Work with Azure Bicep Infrastructure as Code (IaC) generation and schema management.

**Parameters:** Same as mcp_azure_mcp_applens

---

## Azure CLI & Templates

### 51. activate_azure_cli_tools
**Description:** Activate tools for generating and installing Azure CLI commands.

**Includes:**
- Generate Azure CLI commands based on goals
- Installation instructions for az, azd, func CLIs

**Parameters:** None

---

### 52. activate_dotnet_project_template_management
**Description:** Activate tools for finding and managing dotnet project templates.

**Includes:**
- `azure_dotnet_templates-get_tags`: Get tags to filter templates
- `azure_dotnet_templates-get_templates_for_tag`: Get templates for a tag

**Parameters:** None

---

### 53. activate_azure_resource_management_tools
**Description:** Activate comprehensive suite for managing Azure resources and services.

**Includes:** Container Registry, Kubernetes Service, App Configuration, Application Insights, Cosmos DB, MySQL, PostgreSQL, Azure Monitor, Datadog, Communication Services, Event Grid, Key Vault, RBAC, Marketplace, Load Testing, Virtual Desktop.

**Parameters:** None

---

## Python Environment Management

### 54. configure_python_environment
**Description:** Configure a Python environment in the workspace. ALWAYS call before using other Python tools.

**Parameters:**
- `resourcePath` (string, optional): Path to Python file/workspace.

**Supports:** venv, virtualenv, conda, pipenv, poetry, pyenv, pixi, etc.

---

### 55. install_python_packages
**Description:** Install Python packages in the workspace. ALWAYS call configure_python_environment first.

**Parameters:**
- `packageList` (array, required): List of Python packages to install.
- `resourcePath` (string, optional): Path to Python file/workspace.

---

### 56. activate_python_environment_tools
**Description:** Activate tools for managing and retrieving Python environment information.

**Includes:**
- `get_python_environment_details`: Get environment type, version, installed packages
- `get_python_executable_details`: Get Python executable path and arguments

**Parameters:** None

---

### 57. configure_notebook
**Description:** Configure a Notebook. ALWAYS use before running cells or installing packages for the first time.

**Parameters:**
- `filePath` (string, required): Absolute path to notebook.

---

### 58. activate_notebook_kernel_configuration
**Description:** Activate tools for configuring Jupyter notebook execution environment.

**Includes:**
- `configure_non_python_notebook`: Select kernel for non-Python languages
- `configure_python_notebook`: Configure Python kernel

**Parameters:** None

---

### 59. activate_notebook_package_management
**Description:** Activate tools for managing Python packages within Jupyter notebooks.

**Includes:**
- `notebook_install_packages`: Install packages into notebook kernel
- `notebook_list_packages`: View installed packages in kernel

**Parameters:** None

---

## Python Analysis & Refactoring

### 60. activate_python_syntax_validation_tools
**Description:** Activate tools for validating and troubleshooting Python code syntax.

**Includes:** Pylance documentation search, syntax error checking.

**Parameters:** None

---

### 61. activate_python_import_analysis_tools
**Description:** Activate tools for analyzing and managing Python imports.

**Includes:** Identify imported modules, detect missing dependencies, check installed modules.

**Parameters:** None

---

### 62. activate_python_environment_management_tools
**Description:** Activate tools for managing Python environments and configurations.

**Includes:** Get active/available environments, analysis settings, switch environments.

**Parameters:** None

---

### 63. activate_python_workspace_management_tools
**Description:** Activate tools for managing and navigating Python workspace.

**Includes:** Get workspace root directories, list user-created Python files.

**Parameters:** None

---

### 64. mcp_pylance_mcp_s_pylanceDocString
**Description:** Get docstring/documentation for a Python symbol.

**Parameters:**
- `fileUri` (string, required): URI of file containing the symbol.
- `symbolName` (string, required): Exact symbol name.

---

### 65. mcp_pylance_mcp_s_pylanceInvokeRefactoring
**Description:** Apply automated code refactoring to Python files.

**Parameters:**
- `fileUri` (string, required): URI of file to refactor.
- `name` (string, required): Refactoring name. Options:
  - `source.unusedImports`: Remove unused imports
  - `source.convertImportFormat`: Convert import format
  - `source.convertImportStar`: Convert wildcard imports
  - `source.convertImportToModule`: Convert to module imports
  - `source.renameShadowedStdlibImports`: Rename shadowed imports
  - `source.addTypeAnnotation`: Add type annotations
  - `source.fixAll.pylance`: Apply all fixes
- `mode` (string, optional): Output mode: `update`, `edits`, or `string`.

---

### 66. mcp_pylance_mcp_s_pylanceImports
**Description:** Analyze imports across workspace user files.

**Parameters:**
- `workspaceRoot` (string, required): Root directory URI of workspace.

---

## Microsoft Documentation

### 67. activate_microsoft_docs_tools
**Description:** Activate tools for retrieving and converting Microsoft documentation.

**Includes:**
- `mcp_microsoftdocs_microsoft_docs_search`: Search Microsoft/Azure docs
- `mcp_microsoftdocs_microsoft_docs_fetch`: Fetch complete doc pages

**Parameters:** None

---

### 68. mcp_microsoftdocs_microsoft_code_sample_search
**Description:** Search for code snippets in official Microsoft Learn documentation.

**Parameters:**
- `query` (string, required): Descriptive query or SDK/method name.
- `language` (string, optional): Programming language filter (csharp, javascript, typescript, python, powershell, azurecli, sql, java, kusto, cpp, go, rust, ruby, php).

---

### 69. mcp_microsoftdocs_microsoft_docs_fetch
**Description:** Fetch and convert Microsoft Learn documentation webpage to markdown.

**Parameters:**
- `url` (string, required): URL of Microsoft documentation page.

**Use after:** microsoft_docs_search when you need complete content.

---

## Specialized Tools

### 70. vscode_askQuestions
**Description:** Ask the user clarifying questions before proceeding.

**Parameters:**
- `questions` (array, required): List of questions, each with:
  - `header` (string): Short identifier (max 50 chars)
  - `question` (string): Question text (max 200 chars)
  - `multiSelect` (boolean, optional): Allow multiple selections
  - `allowFreeformInput` (boolean, optional): Allow freeform text
  - `options` (array, optional): Selectable answers

---

### 71. vscode_listCodeUsages
**Description:** Find all usages (references, definitions, implementations) of a code symbol.

**Parameters:**
- `symbol` (string, required): Exact symbol name.
- `uri` (string, optional): Full URI of file where symbol appears.
- `filePath` (string, optional): Workspace-relative file path.
- `lineContent` (string, required): Substring of line containing symbol.

**Supported for:** chatagent, instructions, json, markdown, prompt, python, skill.

---

### 72. vscode_renameSymbol
**Description:** Rename a code symbol across the workspace using language server.

**Parameters:**
- `symbol` (string, required): Current symbol name.
- `newName` (string, required): New symbol name.
- `uri` (string, optional): Full URI of file where symbol appears.
- `filePath` (string, optional): Workspace-relative file path.
- `lineContent` (string, required): Substring of line containing symbol.

**Supported for:** chatagent, instructions, markdown, prompt, python, skill.

---

### 73. renderMermaidDiagram
**Description:** Render a Mermaid diagram from Mermaid.js markup.

**Parameters:**
- `markup` (string, optional): Mermaid diagram markup (no code block wrapper).
- `title` (string, optional): Short title for the diagram.

---

### 74. test_failure
**Description:** Include test failure information in the prompt.

**Parameters:** None

---

### 75. open_browser_page
**Description:** Open a new browser page in the integrated browser.

**Parameters:**
- `url` (string, required): Full URL to open.

---

## Subagent

### 76. runSubagent
**Description:** Launch a new agent to handle complex, multi-step tasks autonomously.

**Parameters:**
- `prompt` (string, required): Detailed task description for the agent.
- `description` (string, required): Short (3-5 word) task description.
- `agentName` (string, optional): Specific agent name to invoke.

**Use for:** Complex research, code searching, multi-step tasks.

**Note:** Agents are stateless and return a single final message.

---

## Summary Statistics

| Category | Count |
|----------|-------|
| File & Directory Management | 5 |
| File Operations | 6 |
| Search & Discovery | 4 |
| Notebook Operations | 5 |
| VS Code Integration | 6 |
| Terminal & Process Management | 6 |
| Memory Management | 2 |
| Task & Todo Management | 2 |
| Azure Authentication & Resources | 3 |
| Azure Services | 11 |
| Azure CLI & Templates | 3 |
| Python Environment Management | 6 |
| Python Analysis & Refactoring | 6 |
| Microsoft Documentation | 3 |
| Specialized Tools | 6 |
| Subagent | 1 |
| **Total** | **76** |

---

## Tool Usage Patterns

### Most Common Workflows

1. **File Editing:**
   - `read_file` → `replace_string_in_file` or `multi_replace_string_in_file`
   - `get_errors` (validate changes)

2. **Python Development:**
   - `configure_python_environment` (ALWAYS FIRST)
   - `install_python_packages`
   - `mcp_pylance_mcp_s_pylanceInvokeRefactoring` (refactor)
   - `get_errors` (validate)

3. **Azure Operations:**
   - `activate_azure_authentication_and_resource_management`
   - `mcp_azure_mcp_applens` (diagnose issues)
   - `azure_bicep-get_azure_verified_module` (get Bicep modules)

4. **Notebook Development:**
   - `configure_notebook` (ALWAYS FIRST)
   - `copilot_getNotebookSummary` (get cell info)
   - `run_notebook_cell` (execute)
   - `read_notebook_cell_output` (check results)

5. **Documentation Research:**
   - `mcp_microsoftdocs_microsoft_code_sample_search` (find code samples)
   - `mcp_microsoftdocs_microsoft_docs_fetch` (get full docs)

---

## Notes

- **Activation Tools:** Many tool groups require activation before use (e.g., `activate_azure_*`, `activate_python_*`).
- **Prerequisites:** Some tools have strict ordering requirements (e.g., `configure_python_environment` before `install_python_packages`).
- **MCP Tools:** Tools prefixed with `mcp_` are Model Context Protocol tools with hierarchical command routing.
- **Background Processes:** Use `isBackground=true` for long-running terminal commands.
- **Memory Scopes:** Three memory tiers provide different persistence levels.

---

**Generated from:** `vscode/panel_editAgent_ab1a6331.copilotmd`  
**Date:** 2026-04-05  
**Model:** claude-haiku-4.5
