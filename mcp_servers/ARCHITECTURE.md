# MCP Servers Architecture

## Overview

This project implements 16 independent FastMCP-based Model Context Protocol servers, each providing specialized tools for different VS Code Copilot functionality categories.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        MCP Client Layer                          │
│  (VS Code Copilot, Custom Clients, HTTP/SSE Clients)           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ MCP Protocol (HTTP/SSE/Stdio)
                              │
┌─────────────────────────────────────────────────────────────────┐
│                     MCP Server Gateway                           │
│                    (Load Balancer/Router)                        │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
┌───────▼────────┐   ┌───────▼────────┐   ┌───────▼────────┐
│  File & Dir    │   │  File Ops      │   │  Search &      │
│  Server        │   │  Server        │   │  Discovery     │
│  Port: 8001    │   │  Port: 8002    │   │  Port: 8003    │
└────────────────┘   └────────────────┘   └────────────────┘

┌────────────────┐   ┌────────────────┐   ┌────────────────┐
│  Notebook      │   │  VS Code       │   │  Terminal &    │
│  Operations    │   │  Integration   │   │  Process Mgmt  │
│  Port: 8004    │   │  Port: 8005    │   │  Port: 8006    │
└────────────────┘   └────────────────┘   └────────────────┘

┌────────────────┐   ┌────────────────┐   ┌────────────────┐
│  Memory        │   │  Task & Todo   │   │  Azure Auth    │
│  Management    │   │  Management    │   │  & Resources   │
│  Port: 8007    │   │  Port: 8008    │   │  Port: 8009    │
└────────────────┘   └────────────────┘   └────────────────┘

┌────────────────┐   ┌────────────────┐   ┌────────────────┐
│  Azure         │   │  Azure CLI     │   │  Python Env    │
│  Services      │   │  & Templates   │   │  Management    │
│  Port: 8010    │   │  Port: 8011    │   │  Port: 8012    │
└────────────────┘   └────────────────┘   └────────────────┘

┌────────────────┐   ┌────────────────┐   ┌────────────────┐
│  Python        │   │  Microsoft     │   │  Specialized   │
│  Analysis      │   │  Docs          │   │  Tools         │
│  Port: 8013    │   │  Port: 8014    │   │  Port: 8015    │
└────────────────┘   └────────────────┘   └────────────────┘

                 ┌────────────────┐
                 │  Subagent      │
                 │  Server        │
                 │  Port: 8016    │
                 └────────────────┘
```

## Server Categories

### 1. File System Operations (Ports 8001-8002)
- **File & Directory Management**: Create, list, search files and directories
- **File Operations**: Read, edit, view images, track changes

### 2. Search & Discovery (Port 8003)
- Semantic search, GitHub integration, web scraping

### 3. Development Tools (Ports 8004-8006)
- **Notebook Operations**: Jupyter notebook management
- **VS Code Integration**: Workspace, extensions, API access
- **Terminal & Process**: Command execution, process management

### 4. State Management (Ports 8007-8008)
- **Memory Management**: Persistent storage across scopes
- **Task & Todo**: Project workflow management

### 5. Cloud Services (Ports 8009-8011)
- **Azure Authentication**: Auth, subscriptions, resources
- **Azure Services**: Bicep, AppLens, Terraform, AI services
- **Azure CLI**: Command generation, templates

### 6. Python Development (Ports 8012-8013)
- **Python Environment**: Environment setup, package management
- **Python Analysis**: Code analysis, refactoring, imports

### 7. Documentation & Specialized (Ports 8014-8015)
- **Microsoft Docs**: Documentation search and retrieval
- **Specialized Tools**: User interaction, code analysis, diagrams

### 8. Agent Orchestration (Port 8016)
- **Subagent**: Autonomous agent execution

## Communication Patterns

### 1. Direct HTTP/SSE
```
Client → HTTP POST → Server → JSON Response
```

### 2. Stdio Transport
```
Client → Stdin → Server → Stdout → Client
```

### 3. Server-to-Server
```
Server A → HTTP → Server B → Response → Server A
```

## Data Flow

```
┌──────────┐
│  Client  │
└────┬─────┘
     │ 1. Tool Request
     ▼
┌──────────────┐
│  MCP Server  │
└────┬─────────┘
     │ 2. Validate Input
     ▼
┌──────────────┐
│  Tool Logic  │
└────┬─────────┘
     │ 3. Execute
     ▼
┌──────────────┐
│  Resources   │ (File System, APIs, Databases)
└────┬─────────┘
     │ 4. Return Result
     ▼
┌──────────────┐
│  Response    │
└──────────────┘
```

## Security Architecture

### Authentication Layers
1. **API Key Authentication** (Optional)
2. **OAuth 2.0** (Azure services)
3. **Token-based Auth** (GitHub, Microsoft Docs)

### Authorization
- Role-based access control (RBAC)
- Resource-level permissions
- Rate limiting per client

### Data Protection
- Input validation and sanitization
- SQL injection prevention
- Path traversal protection
- Secure credential storage

## Scalability

### Horizontal Scaling
```
Load Balancer
    ├── Server Instance 1 (Ports 8001-8016)
    ├── Server Instance 2 (Ports 8001-8016)
    └── Server Instance N (Ports 8001-8016)
```

### Vertical Scaling
- Increase server resources (CPU, RAM)
- Optimize tool implementations
- Implement caching layers

### Caching Strategy
```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
┌──────▼──────┐
│  Redis      │ (Cache Layer)
│  Cache      │
└──────┬──────┘
       │ Cache Miss
┌──────▼──────┐
│  MCP Server │
└─────────────┘
```

## Monitoring & Observability

### Metrics
- Request count per tool
- Response time (p50, p95, p99)
- Error rate
- Active connections

### Logging
```
[2024-01-01 12:00:00] INFO: Tool executed: create_directory
[2024-01-01 12:00:01] ERROR: Failed to create directory: Permission denied
```

### Tracing
- Distributed tracing with OpenTelemetry
- Request ID propagation
- Performance profiling

## Deployment Strategies

### 1. Docker Compose (Development)
```bash
docker-compose up -d
```

### 2. Kubernetes (Production)
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mcp-file-directory-server
spec:
  replicas: 3
  selector:
    matchLabels:
      app: mcp-file-directory
  template:
    metadata:
      labels:
        app: mcp-file-directory
    spec:
      containers:
      - name: server
        image: mcp-file-directory:latest
        ports:
        - containerPort: 8001
```

### 3. Serverless (AWS Lambda, Azure Functions)
- Event-driven execution
- Auto-scaling
- Pay-per-use pricing

## Error Handling

### Error Response Format
```json
{
  "success": false,
  "error": "Error message",
  "error_code": "ERR_FILE_NOT_FOUND",
  "details": {
    "path": "/invalid/path",
    "timestamp": "2024-01-01T12:00:00Z"
  }
}
```

### Retry Strategy
- Exponential backoff
- Maximum retry attempts: 3
- Retry on: 5xx errors, network timeouts

## Performance Optimization

### 1. Connection Pooling
- Reuse database connections
- HTTP connection pooling
- WebSocket connection management

### 2. Async Operations
- Non-blocking I/O
- Concurrent request handling
- Background task processing

### 3. Resource Management
- Memory limits per server
- CPU throttling
- Disk I/O optimization

## Testing Strategy

### Unit Tests
```python
@pytest.mark.asyncio
async def test_create_directory():
    result = await create_directory("/tmp/test")
    assert result["success"] == True
```

### Integration Tests
```python
@pytest.mark.asyncio
async def test_file_workflow():
    # Create directory
    await client.call_tool("create_directory", {"dirPath": "/tmp/test"})
    
    # Create file
    await client.call_tool("create_file", {
        "filePath": "/tmp/test/file.txt",
        "content": "test"
    })
    
    # Verify
    result = await client.call_tool("list_dir", {"path": "/tmp/test"})
    assert "file.txt" in result["contents"]
```

### Load Tests
- Concurrent requests: 1000
- Duration: 5 minutes
- Target: <100ms p95 latency

## Future Enhancements

1. **GraphQL API** - Alternative to REST
2. **WebSocket Support** - Real-time updates
3. **gRPC Protocol** - High-performance RPC
4. **Event Streaming** - Kafka/RabbitMQ integration
5. **AI/ML Integration** - Intelligent tool suggestions
6. **Multi-tenancy** - Isolated environments per tenant
7. **Audit Logging** - Compliance and security
8. **API Gateway** - Unified entry point

## References

- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [Model Context Protocol Spec](https://modelcontextprotocol.io)
- [VS Code Extension API](https://code.visualstudio.com/api)
