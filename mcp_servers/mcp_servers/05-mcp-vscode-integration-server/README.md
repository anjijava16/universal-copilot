# VS Code Integration Server 🔧

Port: 8005

## Features

- **create_new_workspace**: Create complete project structure
- **get_project_setup_info**: Get project setup information
- **get_vscode_api**: Get VS Code API documentation
- **install_extension**: Install VS Code extension
- **run_vscode_command**: Run VS Code command
- **vscode_searchExtensions_internal**: Search VS Code extensions

## Installation

```bash
pip install -r requirements.txt
```

## Running the Server

```bash
# Default port 8005
python server.py

# Custom port
PORT=9000 python server.py
```

## Tools


### 1. create_new_workspace

Create complete project structure

```python
await client.call_tool("create_new_workspace", {
    # Add parameters here
})
```

### 2. get_project_setup_info

Get project setup information

```python
await client.call_tool("get_project_setup_info", {
    # Add parameters here
})
```

### 3. get_vscode_api

Get VS Code API documentation

```python
await client.call_tool("get_vscode_api", {
    # Add parameters here
})
```

### 4. install_extension

Install VS Code extension

```python
await client.call_tool("install_extension", {
    # Add parameters here
})
```

### 5. run_vscode_command

Run VS Code command

```python
await client.call_tool("run_vscode_command", {
    # Add parameters here
})
```

### 6. vscode_searchExtensions_internal

Search VS Code extensions

```python
await client.call_tool("vscode_searchExtensions_internal", {
    # Add parameters here
})
```


## Configuration

Environment variables:

- `PORT`: Server port (default: 8005)
- `LOG_LEVEL`: Logging level (default: INFO)

## License

MIT
