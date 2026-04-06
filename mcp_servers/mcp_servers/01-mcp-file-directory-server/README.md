# File & Directory Management Server 📂

Port: 8001

## Features

- **create_directory**: Create directory structure recursively
- **create_file**: Create new file with content
- **list_dir**: List directory contents
- **file_search**: Search files by glob pattern
- **grep_search**: Search file contents by text/regex

## Installation

```bash
pip install -r requirements.txt
```

## Running the Server

```bash
# Default port 8001
python server.py

# Custom port
PORT=9000 python server.py
```

## Tools


### 1. create_directory

Create directory structure recursively

```python
await client.call_tool("create_directory", {
    # Add parameters here
})
```

### 2. create_file

Create new file with content

```python
await client.call_tool("create_file", {
    # Add parameters here
})
```

### 3. list_dir

List directory contents

```python
await client.call_tool("list_dir", {
    # Add parameters here
})
```

### 4. file_search

Search files by glob pattern

```python
await client.call_tool("file_search", {
    # Add parameters here
})
```

### 5. grep_search

Search file contents by text/regex

```python
await client.call_tool("grep_search", {
    # Add parameters here
})
```


## Configuration

Environment variables:

- `PORT`: Server port (default: 8001)
- `LOG_LEVEL`: Logging level (default: INFO)

## License

MIT
