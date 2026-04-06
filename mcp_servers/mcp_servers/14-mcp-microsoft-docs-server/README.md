# Microsoft Documentation Server 📚

Port: 8014

## Features

- **activate_microsoft_docs_tools**: Activate docs tools
- **mcp_microsoftdocs_microsoft_code_sample_search**: Search code samples
- **mcp_microsoftdocs_microsoft_docs_fetch**: Fetch documentation page

## Installation

```bash
pip install -r requirements.txt
```

## Running the Server

```bash
# Default port 8014
python server.py

# Custom port
PORT=9000 python server.py
```

## Tools


### 1. activate_microsoft_docs_tools

Activate docs tools

```python
await client.call_tool("activate_microsoft_docs_tools", {
    # Add parameters here
})
```

### 2. mcp_microsoftdocs_microsoft_code_sample_search

Search code samples

```python
await client.call_tool("mcp_microsoftdocs_microsoft_code_sample_search", {
    # Add parameters here
})
```

### 3. mcp_microsoftdocs_microsoft_docs_fetch

Fetch documentation page

```python
await client.call_tool("mcp_microsoftdocs_microsoft_docs_fetch", {
    # Add parameters here
})
```


## Configuration

Environment variables:

- `PORT`: Server port (default: 8014)
- `LOG_LEVEL`: Logging level (default: INFO)

## License

MIT
