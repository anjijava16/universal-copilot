# Azure Services Server 🌐

Port: 8010

## Features

- **azure_bicep_get_azure_verified_module**: Get Bicep module
- **mcp_azure_mcp_applens**: AppLens diagnostics
- **mcp_azure_mcp_azureterraformbestpractices**: Terraform best practices
- **mcp_azure_mcp_confidentialledger**: Confidential Ledger operations
- **mcp_azure_mcp_resourcehealth**: Resource health monitoring
- **mcp_azure_mcp_speech**: Azure AI Speech operations

## Installation

```bash
pip install -r requirements.txt
```

## Running the Server

```bash
# Default port 8010
python server.py

# Custom port
PORT=9000 python server.py
```

## Tools


### 1. azure_bicep_get_azure_verified_module

Get Bicep module

```python
await client.call_tool("azure_bicep_get_azure_verified_module", {
    # Add parameters here
})
```

### 2. mcp_azure_mcp_applens

AppLens diagnostics

```python
await client.call_tool("mcp_azure_mcp_applens", {
    # Add parameters here
})
```

### 3. mcp_azure_mcp_azureterraformbestpractices

Terraform best practices

```python
await client.call_tool("mcp_azure_mcp_azureterraformbestpractices", {
    # Add parameters here
})
```

### 4. mcp_azure_mcp_confidentialledger

Confidential Ledger operations

```python
await client.call_tool("mcp_azure_mcp_confidentialledger", {
    # Add parameters here
})
```

### 5. mcp_azure_mcp_resourcehealth

Resource health monitoring

```python
await client.call_tool("mcp_azure_mcp_resourcehealth", {
    # Add parameters here
})
```

### 6. mcp_azure_mcp_speech

Azure AI Speech operations

```python
await client.call_tool("mcp_azure_mcp_speech", {
    # Add parameters here
})
```


## Configuration

Environment variables:

- `PORT`: Server port (default: 8010)
- `LOG_LEVEL`: Logging level (default: INFO)

## License

MIT
