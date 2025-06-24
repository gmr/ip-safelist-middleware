# IP Safelist Middleware

FastAPI Middleware for IP Address Safelisting. This middleware allows you to restrict access to your FastAPI application based on client IP addresses.

## Features

- 🛡️ **IP address filtering** based on exact match or network ranges (CIDR notation)
- 🌐 **AWS IP ranges support** from specified regions
- 🎯 **Path-based access control** using regex patterns
- 🔓 **Unrestricted access** for public endpoints using `allow` type
- ⚙️ **Environment variable configuration** with pydantic-settings
- 🔧 **Customizable HTTP status code and message** for blocked requests

## Quick Start

```bash
pip install ip-safelist-middleware
```

```python
from fastapi import FastAPI
from ip_safelist_middleware import IPSafeListMiddleware, ListItem, ListType

app = FastAPI()

# Basic IP filtering
app.add_middleware(
    IPSafeListMiddleware,
    list_items=[
        ListItem(path=r'^/api/.*$', type=ListType.env),
    ]
)
```

Set allowed IPs via environment variable:
```bash
export IP_SAFELIST_NETWORKS="127.0.0.1,192.168.0.0/24,10.0.0.0/8"
```

## Use Cases

- **API Security**: Restrict API access to specific IP ranges
- **Admin Panels**: Limit administrative interfaces to internal networks
- **Development/Staging**: Control access to non-production environments
- **Compliance**: Meet security requirements for IP-based access control
- **Load Balancer Health Checks**: Allow unrestricted access to health endpoints

## Why IP Safelist Middleware?

While IP-based filtering shouldn't be your only security layer, it provides an important first line of defense by:

- Reducing attack surface by blocking unwanted traffic at the application level
- Providing simple access control for internal tools and APIs
- Supporting both static IP lists and dynamic AWS IP ranges
- Offering flexible path-based rules for different endpoint requirements

## Next Steps

- [Getting Started](getting-started.md) - Detailed setup instructions
- [Configuration](configuration.md) - Environment variables and options
- [Examples](examples.md) - Real-world usage patterns
- [API Reference](api-reference.md) - Complete API documentation
