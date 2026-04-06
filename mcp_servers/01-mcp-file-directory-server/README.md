# MCP File & Directory Management Server 📂

A FastMCP-based server providing comprehensive file system operations through the Model Context Protocol.

## Features

- **Directory Creation**: Recursive directory creation (mkdir -p)
- **File Creation**: Create files with content, auto-create parent directories
- **Directory Listing**: List directory contents with type indicators
- **File Search**: Glob pattern-based file searching
- **Grep Search**: Text/regex search across file contents

## Installation

```bash
pip install -r requirements.txt
```

## Running the Server

```bash
# Default port 8001
python server.py

# Custom port
PORT=9001 python server.py
```

## Tools

### 1. create_directory

Create a new directory structure recursively.

```python
await client.call_tool("create_directory", {
    "dirPath": "/path/to/new/directory"
})
```

### 2. create_file

Create a new file with specified content.

```python
await client.call_tool("create_file", {
    "filePath": "/path/to/file.txt",
    "content": "Hello, World!"
})
```

### 3. list_dir

List directory contents (folders end with /).

```python
await client.call_tool("list_dir", {
    "path": "/path/to/directory"
})
```

### 4. file_search

Search files by glob pattern.

```python
# Find all Python files
await client.call_tool("file_search", {
    "query": "**/*.py",
    "maxResults": 100
})

# Find all JS/TS files
await client.call_tool("file_search", {
    "query": "**/*.{js,ts}"
})
```

### 5. grep_search

Search file contents by text or regex.

```python
# Text search
await client.call_tool("grep_search", {
    "query": "TODO",
    "isRegexp": False,
    "includePattern": "**/*.py",
    "maxResults": 50
})

# Regex search
await client.call_tool("grep_search", {
    "query": "function\\s+\\w+",
    "isRegexp": True,
    "includePattern": "**/*.js"
})
```

## Configuration

Environment variables:

- `PORT`: Server port (default: 8001)
- `LOG_LEVEL`: Logging level (default: INFO)

## Examples

### Create Project Structure

```python
# Create directories
await client.call_tool("create_directory", {"dirPath": "./src"})
await client.call_tool("create_directory", {"dirPath": "./tests"})

# Create files
await client.call_tool("create_file", {
    "filePath": "./src/main.py",
    "content": "def main():\n    print('Hello')\n"
})
```

### Search and List

```python
# Find all markdown files
result = await client.call_tool("file_search", {
    "query": "**/*.md"
})

# Search for TODOs
result = await client.call_tool("grep_search", {
    "query": "TODO|FIXME",
    "isRegexp": True
})
```

## License

MIT
