# Search & Discovery Server 🔍

Port: 8003

## Features

- **semantic_search**: Natural language code search
- **get_search_view_results**: Get search view results
- **github_repo**: Search GitHub repository
- **fetch_webpage**: Fetch webpage content

## Installation

```bash
pip install -r requirements.txt
```

## Running the Server

```bash
# Default port 8003
python server.py

# Custom port
PORT=9000 python server.py
```

## Tools


### 1. semantic_search

Natural language code search

```python
await client.call_tool("semantic_search", {
    # Add parameters here
})
```

### 2. get_search_view_results

Get search view results

```python
await client.call_tool("get_search_view_results", {
    # Add parameters here
})
```

### 3. github_repo

Search GitHub repository

```python
await client.call_tool("github_repo", {
    # Add parameters here
})
```

### 4. fetch_webpage

Fetch webpage content

```python
await client.call_tool("fetch_webpage", {
    # Add parameters here
})
```


## Configuration

Environment variables:

- `PORT`: Server port (default: 8003)
- `LOG_LEVEL`: Logging level (default: INFO)

## License

MIT
