# Terminal & Process Management Server 💻

Port: 8006

## Features

- **run_in_terminal**: Execute shell command
- **await_terminal**: Wait for background command
- **get_terminal_output**: Get terminal output
- **kill_terminal**: Kill terminal process
- **terminal_last_command**: Get last command
- **terminal_selection**: Get terminal selection

## Installation

```bash
pip install -r requirements.txt
```

## Running the Server

```bash
# Default port 8006
python server.py

# Custom port
PORT=9000 python server.py
```

## Tools


### 1. run_in_terminal

Execute shell command

```python
await client.call_tool("run_in_terminal", {
    # Add parameters here
})
```

### 2. await_terminal

Wait for background command

```python
await client.call_tool("await_terminal", {
    # Add parameters here
})
```

### 3. get_terminal_output

Get terminal output

```python
await client.call_tool("get_terminal_output", {
    # Add parameters here
})
```

### 4. kill_terminal

Kill terminal process

```python
await client.call_tool("kill_terminal", {
    # Add parameters here
})
```

### 5. terminal_last_command

Get last command

```python
await client.call_tool("terminal_last_command", {
    # Add parameters here
})
```

### 6. terminal_selection

Get terminal selection

```python
await client.call_tool("terminal_selection", {
    # Add parameters here
})
```


## Configuration

Environment variables:

- `PORT`: Server port (default: 8006)
- `LOG_LEVEL`: Logging level (default: INFO)

## License

MIT
