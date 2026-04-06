# Memory Management Server 🧠

Port: 8007

## Features

- **memory**: Manage persistent memory
- **resolve_memory_file_uri**: Resolve memory file URI

## Installation

```bash
pip install -r requirements.txt
```

## Running the Server

```bash
# Default port 8007
python server.py

# Custom port
PORT=9000 python server.py
```

## Tools


### 1. memory

Manage persistent memory

```python
await client.call_tool("memory", {
    # Add parameters here
})
```

### 2. resolve_memory_file_uri

Resolve memory file URI

```python
await client.call_tool("resolve_memory_file_uri", {
    # Add parameters here
})
```


## Configuration

Environment variables:

- `PORT`: Server port (default: 8007)
- `LOG_LEVEL`: Logging level (default: INFO)

## License

MIT
