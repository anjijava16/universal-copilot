# Subagent Server 🤖

Port: 8016

## Features

- **runSubagent**: Launch autonomous agent

## Installation

```bash
pip install -r requirements.txt
```

## Running the Server

```bash
# Default port 8016
python server.py

# Custom port
PORT=9000 python server.py
```

## Tools


### 1. runSubagent

Launch autonomous agent

```python
await client.call_tool("runSubagent", {
    # Add parameters here
})
```


## Configuration

Environment variables:

- `PORT`: Server port (default: 8016)
- `LOG_LEVEL`: Logging level (default: INFO)

## License

MIT
