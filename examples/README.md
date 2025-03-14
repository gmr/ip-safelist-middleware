# FastAPI IP Safelist Middleware Examples

This directory contains example applications demonstrating how to use the FastAPI IP Safelist Middleware.

## Basic App Example

The `basic_app.py` example shows a simple FastAPI application with IPSafeListMiddleware applied. It demonstrates:

1. Setting up the middleware with path-based regex patterns
2. Using environment variable-based IP safelisting
3. Excluding specific paths from the safelist check (health endpoint)
4. Accessing client IP information within route handlers
5. Customizing the HTTP status code and message for blocked requests

### Running the Example

To run the example, install the required dependencies and run the application:

```bash
# First, install the package in development mode
pip install -e ..

# Then install uvicorn if not already installed
pip install uvicorn

# Configure the environment variables for allowed IPs and response
export IP_SAFELIST_NETWORKS="127.0.0.1,::1,192.168.0.0/24"
export IP_SAFELIST_STATUS_CODE=403
export IP_SAFELIST_STATUS_MESSAGE="Access denied: IP not in safelist"

# Run the application
python basic_app.py
```

The server will start on http://0.0.0.0:8000 and only accept connections from:
- 127.0.0.1 (localhost)
- ::1 (localhost IPv6)
- 192.168.0.0/24 network

The `/health` endpoint will be accessible from any IP address due to the regex pattern that excludes it from the safelist check (`^/(?!health).*$`).

### Customizing Error Responses

You can customize the HTTP status code and message returned to blocked requests either:

1. Through environment variables:
   ```bash
   export IP_SAFELIST_STATUS_CODE=401
   export IP_SAFELIST_STATUS_MESSAGE="Unauthorized access"
   ```

2. Directly in code:
   ```python
   app.add_middleware(
       IPSafeListMiddleware,
       list_items=[...],
       status_code=401,
       status_message="Unauthorized: Your IP is not allowed"
   )
   ```

The middleware will return this status code and message to any client whose IP address is not in the safelist for the requested path.
