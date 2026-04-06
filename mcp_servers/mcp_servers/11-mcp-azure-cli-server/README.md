# Azure CLI & Templates Server ⚙️

Port: 8011

## Features

- **activate_azure_cli_tools**: Activate Azure CLI tools
- **activate_dotnet_project_template_management**: Activate .NET template tools

## Installation

```bash
pip install -r requirements.txt
```

## Running the Server

```bash
# Default port 8011
python server.py

# Custom port
PORT=9000 python server.py
```

## Tools


### 1. activate_azure_cli_tools

Activate Azure CLI tools

```python
await client.call_tool("activate_azure_cli_tools", {
    # Add parameters here
})
```

### 2. activate_dotnet_project_template_management

Activate .NET template tools

```python
await client.call_tool("activate_dotnet_project_template_management", {
    # Add parameters here
})
```


## Configuration

Environment variables:

- `PORT`: Server port (default: 8011)
- `LOG_LEVEL`: Logging level (default: INFO)

## License

MIT
