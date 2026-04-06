# Specialized Tools Server 🛠️

Port: 8015

## Features

- **vscode_askQuestions**: Ask user questions
- **vscode_listCodeUsages**: Find code symbol usages
- **renderMermaidDiagram**: Render Mermaid diagram

## Installation

```bash
pip install -r requirements.txt
```

## Running the Server

```bash
# Default port 8015
python server.py

# Custom port
PORT=9000 python server.py
```

## Tools


### 1. vscode_askQuestions

Ask user questions

```python
await client.call_tool("vscode_askQuestions", {
    # Add parameters here
})
```

### 2. vscode_listCodeUsages

Find code symbol usages

```python
await client.call_tool("vscode_listCodeUsages", {
    # Add parameters here
})
```

### 3. renderMermaidDiagram

Render Mermaid diagram

```python
await client.call_tool("renderMermaidDiagram", {
    # Add parameters here
})
```


## Configuration

Environment variables:

- `PORT`: Server port (default: 8015)
- `LOG_LEVEL`: Logging level (default: INFO)

## License

MIT
