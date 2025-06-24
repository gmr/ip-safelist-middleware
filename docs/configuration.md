# Configuration

## Environment Variables

The middleware can be configured using environment variables for easy deployment and configuration management.

### IP Networks Configuration

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `IP_SAFELIST_NETWORKS` | Comma-separated list of IP addresses or CIDR blocks | `None` | `"127.0.0.1,192.168.0.0/24,10.0.0.0/8"` |

### AWS Configuration

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `IP_SAFELIST_AWS_ENABLED` | Enable/disable AWS IP ranges | `False` | `"true"` |
| `IP_SAFELIST_AWS_REGIONS` | Comma-separated list of AWS regions | `"us-east-1,us-east-2"` | `"us-west-1,eu-west-1"` |

### Response Configuration

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `IP_SAFELIST_STATUS_CODE` | HTTP status code for blocked requests | `403` | `"401"` |
| `IP_SAFELIST_STATUS_MESSAGE` | Message returned for blocked requests | `"Forbidden"` | `"Access denied"` |

## Programmatic Configuration

### Basic Setup

```python
from ip_safelist_middleware import IPSafeListMiddleware, ListItem, ListType

app.add_middleware(
    IPSafeListMiddleware,
    list_items=[
        ListItem(path=r'^/api/.*$', type=ListType.env),
    ],
    # Override defaults
    status_code=401,
    status_message="Unauthorized access",
    # Direct IP configuration (bypasses environment variables)
    networks={"192.168.1.0/24", "10.0.0.0/8"},
    # AWS configuration
    aws_enabled=True,
    aws_regions=["us-east-1", "us-west-2"]
)
```

### Multiple List Items

Configure different rules for different paths:

```python
app.add_middleware(
    IPSafeListMiddleware,
    list_items=[
        # Admin requires AWS IPs
        ListItem(path=r'^/admin/.*$', type=ListType.aws),

        # API requires environment IPs
        ListItem(path=r'^/api/.*$', type=ListType.env),

        # Public endpoints allow all
        ListItem(path=r'^/public/.*$', type=ListType.allow),

        # Health checks from environment IPs only
        ListItem(path=r'^/health.*$', type=ListType.env),
    ]
)
```

### Combined List Types

Mix different allowlist types for a single path:

```python
ListItem(
    path=r'^/api/.*$',
    type=[ListType.aws, ListType.env]  # Allow both AWS and environment IPs
)
```

!!! warning "Allow Type Precedence"
    When `ListType.allow` is combined with other types, it takes precedence and grants unrestricted access.

## List Types

### `ListType.env`
Uses IP addresses from environment variables or programmatic configuration.

```python
# Via environment
export IP_SAFELIST_NETWORKS="192.168.1.0/24,10.0.0.1"

# Via code
networks={"192.168.1.0/24", "10.0.0.1"}
```

### `ListType.aws`
Uses IP ranges from AWS regions. Automatically fetches and caches AWS IP ranges.

```python
# Via environment
export IP_SAFELIST_AWS_ENABLED=true
export IP_SAFELIST_AWS_REGIONS="us-east-1,us-west-2"

# Via code
aws_enabled=True
aws_regions=["us-east-1", "us-west-2"]
```

### `ListType.allow`
Bypasses all IP restrictions for matched paths.

```python
ListItem(path=r'^/public/.*$', type=ListType.allow)
```

## Advanced Path Patterns

### Excluding Specific Paths

Use negative lookahead to exclude paths from filtering:

```python
# Apply to all paths except /health and /metrics
ListItem(path=r'^/(?!health|metrics).*$', type=ListType.env)
```

### Multiple Exclusions

```python
# Exclude multiple health-check style endpoints
ListItem(path=r'^/(?!health|ready|live|metrics).*$', type=ListType.env)
```

### Path Priorities

The middleware processes list items in order. More specific patterns should come first:

```python
list_items=[
    # Specific pattern first
    ListItem(path=r'^/api/public/.*$', type=ListType.allow),

    # General pattern second
    ListItem(path=r'^/api/.*$', type=ListType.env),
]
```

## IP Address Formats

### Individual IPs
```bash
export IP_SAFELIST_NETWORKS="192.168.1.1,10.0.0.1,172.16.0.1"
```

### CIDR Blocks
```bash
export IP_SAFELIST_NETWORKS="192.168.0.0/24,10.0.0.0/8,172.16.0.0/12"
```

### Mixed Format
```bash
export IP_SAFELIST_NETWORKS="127.0.0.1,192.168.0.0/24,10.1.1.1"
```

### IPv6 Support
```bash
export IP_SAFELIST_NETWORKS="::1,2001:db8::/32"
```

## Error Handling

The middleware gracefully handles configuration errors:

- **Invalid IP addresses**: Logs warning and skips invalid entries
- **AWS fetch failures**: Falls back to environment IPs if available
- **Empty configuration**: Blocks all requests (fail-safe)

## Performance Considerations

- **AWS IP ranges**: Cached for 24 hours to minimize API calls
- **IP matching**: Uses efficient set-based lookups
- **Regex compilation**: Patterns are compiled once at startup

## Deployment Examples

### Docker Environment
```dockerfile
ENV IP_SAFELIST_NETWORKS="10.0.0.0/8,172.16.0.0/12"
ENV IP_SAFELIST_STATUS_CODE="401"
ENV IP_SAFELIST_STATUS_MESSAGE="Unauthorized"
```

### Kubernetes ConfigMap
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  IP_SAFELIST_NETWORKS: "10.244.0.0/16,10.96.0.0/12"
  IP_SAFELIST_AWS_ENABLED: "true"
  IP_SAFELIST_AWS_REGIONS: "us-west-2"
```

### AWS Lambda Environment
```python
import os
os.environ['IP_SAFELIST_AWS_ENABLED'] = 'true'
os.environ['IP_SAFELIST_AWS_REGIONS'] = 'us-east-1'
```
