# Azure Authentication & Resources Server ☁️

Port: 8009

## Features

- **activate_azure_authentication_and_resource_management**: Activate Azure auth tools
- **azureResources_getAzureActivityLog**: Get Azure activity log
- **activate_azure_subscription_and_resource_group_tools**: Activate subscription tools

## Installation

```bash
pip install -r requirements.txt
```

## Running the Server

```bash
# Default port 8009
python server.py

# Custom port
PORT=9000 python server.py
```

## Tools


### 1. activate_azure_authentication_and_resource_management

Activate Azure auth tools

```python
await client.call_tool("activate_azure_authentication_and_resource_management", {
    # Add parameters here
})
```

### 2. azureResources_getAzureActivityLog

Get Azure activity log

```python
await client.call_tool("azureResources_getAzureActivityLog", {
    # Add parameters here
})
```

### 3. activate_azure_subscription_and_resource_group_tools

Activate subscription tools

```python
await client.call_tool("activate_azure_subscription_and_resource_group_tools", {
    # Add parameters here
})
```


## Configuration

Environment variables:

- `PORT`: Server port (default: 8009)
- `LOG_LEVEL`: Logging level (default: INFO)

## License

MIT
