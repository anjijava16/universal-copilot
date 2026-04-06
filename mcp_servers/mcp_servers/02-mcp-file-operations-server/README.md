# File Operations Server 📝

Port: 8002

## Features

- **read_file**: Read file contents with line range
- **replace_string_in_file**: Replace text in file
- **multi_replace_string_in_file**: Multiple replacements in one call
- **view_image**: View image file contents
- **get_changed_files**: Get git diffs
- **get_errors**: Get compile/lint errors

## Installation

```bash
pip install -r requirements.txt
```

## Running the Server

```bash
# Default port 8002
python server.py

# Custom port
PORT=9000 python server.py
```

## Tools


### 1. read_file

Read file contents with line range

```python
await client.call_tool("read_file", {
    # Add parameters here
})
```

### 2. replace_string_in_file

Replace text in file

```python
await client.call_tool("replace_string_in_file", {
    # Add parameters here
})
```

### 3. multi_replace_string_in_file

Multiple replacements in one call

```python
await client.call_tool("multi_replace_string_in_file", {
    # Add parameters here
})
```

### 4. view_image

View image file contents

```python
await client.call_tool("view_image", {
    # Add parameters here
})
```

### 5. get_changed_files

Get git diffs

```python
await client.call_tool("get_changed_files", {
    # Add parameters here
})
```

### 6. get_errors

Get compile/lint errors

```python
await client.call_tool("get_errors", {
    # Add parameters here
})
```


## Configuration

Environment variables:

- `PORT`: Server port (default: 8002)
- `LOG_LEVEL`: Logging level (default: INFO)

## License

MIT
