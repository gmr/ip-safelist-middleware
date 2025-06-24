# API Reference

Complete API documentation for the IP Safelist Middleware.

## IPSafeListMiddleware

::: ip_safelist_middleware.IPSafeListMiddleware

## ListItem

::: ip_safelist_middleware.ListItem

## ListType

::: ip_safelist_middleware.ListType

## Settings

The middleware uses internal settings that can be configured via environment variables or constructor parameters. See the [Configuration](configuration.md) page for details.

## Exceptions

The middleware may raise standard FastAPI/Starlette HTTP exceptions:

- `HTTPException` with status code 403 (or configured status code) when IP is not allowed
- Various internal exceptions during initialization if configuration is invalid

## Usage Examples

### Basic Middleware Setup

```python
from ip_safelist_middleware import IPSafeListMiddleware, ListItem, ListType

# Simple environment-based filtering
app.add_middleware(
    IPSafeListMiddleware,
    list_items=[
        ListItem(path=r'^/api/.*$', type=ListType.env)
    ]
)
```

### Advanced Configuration

```python
# Complex multi-type configuration
app.add_middleware(
    IPSafeListMiddleware,
    list_items=[
        ListItem(path=r'^/admin/.*$', type=ListType.env),
        ListItem(path=r'^/api/.*$', type=[ListType.aws, ListType.env]),
        ListItem(path=r'^/public/.*$', type=ListType.allow),
    ],
    status_code=401,
    status_message="Unauthorized",
    aws_enabled=True,
    aws_regions=["us-east-1", "us-west-2"],
    networks={"192.168.1.0/24", "10.0.0.0/8"}
)
```

## Environment Variables

All configuration can be provided via environment variables:

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `IP_SAFELIST_NETWORKS` | str | `None` | Comma-separated IP addresses/CIDR blocks |
| `IP_SAFELIST_AWS_ENABLED` | bool | `False` | Enable AWS IP range fetching |
| `IP_SAFELIST_AWS_REGIONS` | str | `"us-east-1,us-east-2"` | Comma-separated AWS regions |
| `IP_SAFELIST_STATUS_CODE` | int | `403` | HTTP status code for blocked requests |
| `IP_SAFELIST_STATUS_MESSAGE` | str | `"Forbidden"` | Response message for blocked requests |

## Type Definitions

### Network Types

The middleware accepts IP addresses and networks in these formats:

- **Individual IPv4**: `192.168.1.1`
- **Individual IPv6**: `2001:db8::1`
- **IPv4 CIDR**: `192.168.0.0/24`
- **IPv6 CIDR**: `2001:db8::/32`

### Path Patterns

Path patterns use Python regular expressions:

- `^/api/.*$` - Matches all paths starting with `/api/`
- `^/(?!health).*$` - Matches all paths except `/health`
- `^/(admin|api)/.*$` - Matches paths starting with `/admin/` or `/api/`

### List Types

#### `ListType.env`
Uses IP addresses from environment variables or direct configuration.

#### `ListType.aws`
Uses IP ranges from specified AWS regions. Automatically fetches current AWS IP ranges.

#### `ListType.allow`
Bypasses all IP restrictions. When combined with other types, takes precedence.

## Internal Methods

!!! warning "Internal API"
    The following methods are internal implementation details and should not be called directly:

- `_load_from_amazon()` - Fetches AWS IP ranges
- `_get_safe_list()` - Retrieves IP ranges for a specific list type
- `_is_ip_allowed()` - Checks if an IP is in allowed ranges
- `_should_check_request()` - Determines if request should be filtered

## Error Handling

The middleware handles various error conditions gracefully:

### Configuration Errors
- Invalid IP addresses in configuration are logged and ignored
- Empty configuration results in blocking all requests (fail-safe)
- Invalid regex patterns raise `ValueError` during initialization

### Runtime Errors
- Missing client IP information defaults to blocking the request
- AWS IP range fetch failures fall back to environment configuration
- Network parsing errors are logged but don't crash the application

### HTTP Responses

Blocked requests receive:
```json
{
  "detail": "Forbidden"  // or configured status_message
}
```

With HTTP status code 403 (or configured status_code).

## Performance Notes

- **Initialization**: IP ranges are processed and cached at startup
- **Request Processing**: Uses efficient set-based IP membership testing
- **AWS Ranges**: Cached for 24 hours with automatic refresh
- **Regex Matching**: Path patterns compiled once at startup

## Thread Safety

The middleware is thread-safe and can be used in multi-threaded ASGI servers like Uvicorn with multiple workers.
