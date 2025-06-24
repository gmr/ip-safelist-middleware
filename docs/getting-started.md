# Getting Started

## Installation

Install the middleware using pip:

```bash
pip install ip-safelist-middleware
```

## Basic Usage

### Environment-Based IP Filtering

The simplest way to get started is using environment variables to define allowed IP addresses:

```python
from fastapi import FastAPI
from ip_safelist_middleware import IPSafeListMiddleware, ListItem, ListType

app = FastAPI()

# Apply IP filtering to all API endpoints
app.add_middleware(
    IPSafeListMiddleware,
    list_items=[
        ListItem(path=r'^/api/.*$', type=ListType.env),
    ]
)

@app.get("/api/data")
async def get_data():
    return {"message": "This endpoint is protected by IP filtering"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}  # Not protected - no matching pattern
```

Set the allowed IP addresses:

```bash
export IP_SAFELIST_NETWORKS="127.0.0.1,192.168.0.0/24,10.0.0.0/8"
```

### AWS IP Ranges

For applications running on AWS, you can automatically allow traffic from specific AWS regions:

```python
app.add_middleware(
    IPSafeListMiddleware,
    list_items=[
        ListItem(path=r'^/admin/.*$', type=ListType.aws),
    ]
)
```

Configure AWS regions:
```bash
export IP_SAFELIST_AWS_REGIONS="us-east-1,us-west-2"
export IP_SAFELIST_AWS_ENABLED=true
```

### Public Endpoints

Use `ListType.allow` to create endpoints that bypass IP restrictions entirely:

```python
app.add_middleware(
    IPSafeListMiddleware,
    list_items=[
        ListItem(path=r'^/api/.*$', type=ListType.env),      # Protected
        ListItem(path=r'^/public/.*$', type=ListType.allow), # Public
        ListItem(path=r'^/docs.*$', type=ListType.allow),    # Public docs
    ]
)
```

## Understanding Path Patterns

The middleware uses regex patterns to match request paths. Here are some common patterns:

| Pattern | Description | Example Matches |
|---------|-------------|-----------------|
| `^/api/.*$` | All paths starting with `/api/` | `/api/users`, `/api/data/items` |
| `^/admin/.*$` | All admin paths | `/admin/dashboard`, `/admin/users` |
| `^/(?!health).*$` | All paths except `/health` | `/api/data` (✓), `/health` (✗) |
| `^/.*$` | All paths (default) | Every endpoint |

!!! tip "Testing Regex Patterns"
    Use online regex testers like [regex101.com](https://regex101.com/) to validate your patterns before deployment.

## Default Behavior

When no configuration is provided, the middleware:

- ✅ Applies to **all paths** (`^/.*$` pattern)
- ✅ Uses **environment-based** IP filtering (`ListType.env`)
- ❌ **Blocks all requests** if no IPs are configured
- ❌ Returns `403 Forbidden` for blocked requests

```python
# This will block ALL requests unless IP_SAFELIST_NETWORKS is set
app.add_middleware(IPSafeListMiddleware)
```

## Error Responses

Customize the response for blocked requests:

```python
app.add_middleware(
    IPSafeListMiddleware,
    list_items=[
        ListItem(path=r'^/api/.*$', type=ListType.env),
    ],
    status_code=401,
    status_message="Unauthorized: IP not allowed"
)
```

## Next Steps

- [Configuration](configuration.md) - Detailed configuration options
- [Examples](examples.md) - Real-world usage patterns
- [API Reference](api-reference.md) - Complete API documentation
