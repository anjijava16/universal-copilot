# Task & Todo Management Server ✅

Port: 8008

## Features

- **manage_todo_list**: Manage structured todo list
- **create_and_run_task**: Create and run VS Code task

## Installation

```bash
pip install -r requirements.txt
```

## Running the Server

```bash
# Default port 8008
python server.py

# Custom port
PORT=9000 python server.py
```

## Tools


### 1. manage_todo_list

Manage structured todo list

```python
await client.call_tool("manage_todo_list", {
    # Add parameters here
})
```

### 2. create_and_run_task

Create and run VS Code task

```python
await client.call_tool("create_and_run_task", {
    # Add parameters here
})
```


## Configuration

Environment variables:

- `PORT`: Server port (default: 8008)
- `LOG_LEVEL`: Logging level (default: INFO)

## License

MIT
