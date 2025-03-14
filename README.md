# ip-safelist-middleware

FastAPI Middleware for IP Address Safelisting. This middleware allows you to restrict access to your FastAPI application based on client IP addresses.

## Features

- IP address filtering based on exact match or network ranges (CIDR notation)
- Support for AWS IP ranges from specified regions
- Path-based access control using regex patterns
- Environment variable configuration with pydantic-settings
- Customizable HTTP status code and message for blocked requests

## Installation

```bash
pip install ip-safelist-middleware
```

## Usage

### Basic Usage with Environment Variables

```python
from fastapi import FastAPI
from ip_safelist_middleware import IPSafeListMiddleware, ListItem, ListType

app = FastAPI()

# Configure the middleware to use environment-based IP safe list
app.add_middleware(
    IPSafeListMiddleware,
    list_items=[
        ListItem(path=r'^/api/.*$', type=ListType.env),
    ]
)
```

Set the environment variable to specify allowed IPs:
```bash
export IP_SAFELIST_NETWORKS="127.0.0.1,192.168.0.0/24,10.0.0.0/8"
```

### Using AWS IP Ranges

```python
from fastapi import FastAPI
from ip_safelist_middleware import IPSafeListMiddleware, ListItem, ListType

app = FastAPI()

# Configure the middleware to use AWS IP ranges for specific paths
app.add_middleware(
    IPSafeListMiddleware,
    list_items=[
        ListItem(path=r'^/admin/.*$', type=ListType.aws),
    ]
)
```

Configure AWS regions through environment variables:
```bash
export IP_SAFELIST_AWS_REGIONS="us-east-1,us-west-2"
```

### Combined Configuration

You can combine different allowlist types for different paths:

```python
from fastapi import FastAPI
from ip_safelist_middleware import IPSafeListMiddleware, ListItem, ListType

app = FastAPI()

app.add_middleware(
    IPSafeListMiddleware,
    list_items=[
        ListItem(path=r'^/admin/.*$', type=ListType.aws),  # AWS IPs for admin
        ListItem(path=r'^/api/internal/.*$', type=ListType.env),  # Environment IPs for internal API
        ListItem(path=r'^/(?!health).*$', type=ListType.env),  # Environment IPs for everything except health
    ]
)
```

### Excluding Paths

To exclude paths (e.g., health checks), use negative lookahead in your regex pattern:

```python
ListItem(path=r'^/(?!health).*$', type=ListType.env)  # All paths except /health
```

### Custom Error Response

You can customize the HTTP status code and message returned to blocked requests:

```python
app.add_middleware(
    IPSafeListMiddleware,
    list_items=[
        ListItem(path=r'^/api/.*$', type=ListType.env),
    ],
    status_code=401,
    status_message="Unauthorized access"
)
```

## Default Behavior

When added to your FastAPI application without any parameters:

- The middleware blocks **all** paths by default (matches pattern `^/.*$`)
- It uses the environment-based allowlist type
- If no IP addresses are specified in the `IP_SAFELIST_NETWORKS` environment variable, all requests will be blocked
- Blocked requests receive a `403 Forbidden` response
- AWS IP ranges are disabled by default

Example of default behavior:
```python
app.add_middleware(IPSafeListMiddleware)  # No parameters - blocks all requests by default
```

To allow any traffic, you must explicitly define allowed IP addresses through environment variables or custom configurations.

## Custom Rules

If you do not use the default path of `^/.*$` and add your own path rules, requests to a path without a defined rule will be refused.

## Configuration

The middleware can be configured using environment variables:

| Environment Variable | Description | Default |
|---------------------|-------------|---------|
| IP_SAFELIST_NETWORKS | Comma-separated list of IP addresses or CIDR blocks | None |
| IP_SAFELIST_AWS_ENABLED | Enable/disable AWS IP ranges | False |
| IP_SAFELIST_AWS_REGIONS | Comma-separated list of AWS regions | us-east-1,us-east-2 |
| IP_SAFELIST_STATUS_CODE | HTTP status code for blocked requests | 403 |
| IP_SAFELIST_STATUS_MESSAGE | Message returned for blocked requests | Forbidden |

## License

This project is licensed under the BSD License - see the LICENSE file for details.
