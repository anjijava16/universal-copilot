# Python Analysis & Refactoring Server 🔬

Port: 8013

## Features

- **activate_python_syntax_validation_tools**: Activate syntax validation
- **activate_python_import_analysis_tools**: Activate import analysis
- **mcp_pylance_mcp_s_pylanceDocString**: Get Python docstring
- **mcp_pylance_mcp_s_pylanceInvokeRefactoring**: Apply code refactoring
- **mcp_pylance_mcp_s_pylanceImports**: Analyze imports

## Installation

```bash
pip install -r requirements.txt
```

## Running the Server

```bash
# Default port 8013
python server.py

# Custom port
PORT=9000 python server.py
```

## Tools


### 1. activate_python_syntax_validation_tools

Activate syntax validation

```python
await client.call_tool("activate_python_syntax_validation_tools", {
    # Add parameters here
})
```

### 2. activate_python_import_analysis_tools

Activate import analysis

```python
await client.call_tool("activate_python_import_analysis_tools", {
    # Add parameters here
})
```

### 3. mcp_pylance_mcp_s_pylanceDocString

Get Python docstring

```python
await client.call_tool("mcp_pylance_mcp_s_pylanceDocString", {
    # Add parameters here
})
```

### 4. mcp_pylance_mcp_s_pylanceInvokeRefactoring

Apply code refactoring

```python
await client.call_tool("mcp_pylance_mcp_s_pylanceInvokeRefactoring", {
    # Add parameters here
})
```

### 5. mcp_pylance_mcp_s_pylanceImports

Analyze imports

```python
await client.call_tool("mcp_pylance_mcp_s_pylanceImports", {
    # Add parameters here
})
```


## Configuration

Environment variables:

- `PORT`: Server port (default: 8013)
- `LOG_LEVEL`: Logging level (default: INFO)

## License

MIT
