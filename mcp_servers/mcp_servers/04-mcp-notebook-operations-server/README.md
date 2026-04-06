# Notebook Operations Server 📓

Port: 8004

## Features

- **create_new_jupyter_notebook**: Generate new Jupyter notebook
- **edit_notebook_file**: Edit notebook cells
- **copilot_getNotebookSummary**: Get notebook cell summary
- **run_notebook_cell**: Run notebook cell
- **read_notebook_cell_output**: Read cell output

## Installation

```bash
pip install -r requirements.txt
```

## Running the Server

```bash
# Default port 8004
python server.py

# Custom port
PORT=9000 python server.py
```

## Tools


### 1. create_new_jupyter_notebook

Generate new Jupyter notebook

```python
await client.call_tool("create_new_jupyter_notebook", {
    # Add parameters here
})
```

### 2. edit_notebook_file

Edit notebook cells

```python
await client.call_tool("edit_notebook_file", {
    # Add parameters here
})
```

### 3. copilot_getNotebookSummary

Get notebook cell summary

```python
await client.call_tool("copilot_getNotebookSummary", {
    # Add parameters here
})
```

### 4. run_notebook_cell

Run notebook cell

```python
await client.call_tool("run_notebook_cell", {
    # Add parameters here
})
```

### 5. read_notebook_cell_output

Read cell output

```python
await client.call_tool("read_notebook_cell_output", {
    # Add parameters here
})
```


## Configuration

Environment variables:

- `PORT`: Server port (default: 8004)
- `LOG_LEVEL`: Logging level (default: INFO)

## License

MIT
