# Python Environment Management Server 🐍

Port: 8012

## Features

- **configure_python_environment**: Configure Python environment
- **install_python_packages**: Install Python packages
- **activate_python_environment_tools**: Activate environment tools
- **configure_notebook**: Configure notebook
- **activate_notebook_kernel_configuration**: Activate kernel configuration
- **activate_notebook_package_management**: Activate package management

## Installation

```bash
pip install -r requirements.txt
```

## Running the Server

```bash
# Default port 8012
python server.py

# Custom port
PORT=9000 python server.py
```

## Tools


### 1. configure_python_environment

Configure Python environment

```python
await client.call_tool("configure_python_environment", {
    # Add parameters here
})
```

### 2. install_python_packages

Install Python packages

```python
await client.call_tool("install_python_packages", {
    # Add parameters here
})
```

### 3. activate_python_environment_tools

Activate environment tools

```python
await client.call_tool("activate_python_environment_tools", {
    # Add parameters here
})
```

### 4. configure_notebook

Configure notebook

```python
await client.call_tool("configure_notebook", {
    # Add parameters here
})
```

### 5. activate_notebook_kernel_configuration

Activate kernel configuration

```python
await client.call_tool("activate_notebook_kernel_configuration", {
    # Add parameters here
})
```

### 6. activate_notebook_package_management

Activate package management

```python
await client.call_tool("activate_notebook_package_management", {
    # Add parameters here
})
```


## Configuration

Environment variables:

- `PORT`: Server port (default: 8012)
- `LOG_LEVEL`: Logging level (default: INFO)

## License

MIT
