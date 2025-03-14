"""Example FastAPI application with IP Safelist Middleware."""

import uvicorn
from fastapi import FastAPI, Request

from ip_safelist_middleware import (
    ListItem,
    ListType,
    IPSafeListMiddleware,
)

# Create FastAPI app
app = FastAPI(
    title='IP Safelist Middleware Example',
    description='A simple example using FastAPI IP Safelist Middleware',
    version='0.1.0',
)

# Configure environment variables:
# IP_SAFELIST_NETWORKS=127.0.0.1,::1,192.168.0.0/24
# IP_SAFELIST_STATUS_CODE=403
# IP_SAFELIST_STATUS_MESSAGE="Access denied: IP not in safelist"

# Add IPSafeListMiddleware
app.add_middleware(
    IPSafeListMiddleware,
    list_items=[
        ListItem(path=r"^/(?!health).*$", type=ListType.env),
    ],
    # Optional: Override default status code and message
    # status_code=401,
    # status_message="Unauthorized: Your IP is not allowed"
)


@app.get('/')
async def root(request: Request):
    """Root endpoint that returns client IP and a greeting."""
    client_ip = request.client.host if request.client else 'Unknown'
    return {
        'message': 'Welcome to the IP Safelist Middleware example!',
        'client_ip': client_ip
    }


@app.get('/health')
async def health():
    """Health check endpoint that bypasses the safelist check."""
    return {'status': 'ok'}


@app.get('/admin')
async def admin(request: Request):
    """Admin endpoint that requires safelist verification."""
    client_ip = request.client.host if request.client else 'Unknown'
    return {
        'message': 'You have access to the admin area',
        'client_ip': client_ip
    }


if __name__ == '__main__':
    uvicorn.run('basic_app:app', host='0.0.0.0', port=8000, reload=True)
