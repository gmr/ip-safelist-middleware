# Examples

This page contains real-world examples showing how to use IP Safelist Middleware in different scenarios.

## Basic API Protection

Protect your API endpoints while keeping health checks accessible:

```python
from fastapi import FastAPI, Request
from ip_safelist_middleware import IPSafeListMiddleware, ListItem, ListType

app = FastAPI()

# Protect all API endpoints, but allow health checks from anywhere
app.add_middleware(
    IPSafeListMiddleware,
    list_items=[
        # API endpoints require approved IPs
        ListItem(path=r'^/api/.*$', type=ListType.env),
        # Health endpoint allows any IP
        ListItem(path=r'^/health$', type=ListType.allow),
    ]
)

@app.get("/api/users")
async def get_users():
    return {"users": ["alice", "bob"]}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

Environment configuration:
```bash
export IP_SAFELIST_NETWORKS="192.168.1.0/24,10.0.0.0/8"
```

## Multi-Tier Security

Different security levels for different parts of your application:

```python
app.add_middleware(
    IPSafeListMiddleware,
    list_items=[
        # Admin panel - most restrictive (specific IPs only)
        ListItem(path=r'^/admin/.*$', type=ListType.env),

        # Internal API - AWS IPs (for microservices)
        ListItem(path=r'^/api/internal/.*$', type=ListType.aws),

        # Public API - wider IP range
        ListItem(path=r'^/api/public/.*$', type=ListType.env),

        # Documentation - unrestricted
        ListItem(path=r'^/docs.*$', type=ListType.allow),
        ListItem(path=r'^/redoc.*$', type=ListType.allow),

        # Monitoring endpoints - specific IPs
        ListItem(path=r'^/metrics$', type=ListType.env),
    ],
    status_code=401,
    status_message="Access denied"
)
```

Environment configuration:
```bash
# Admin and monitoring IPs (very restrictive)
export IP_SAFELIST_NETWORKS="192.168.1.100,192.168.1.101,10.0.1.0/24"

# AWS regions for internal services
export IP_SAFELIST_AWS_ENABLED=true
export IP_SAFELIST_AWS_REGIONS="us-east-1,us-west-2"
```

## Development vs Production

Conditional configuration based on environment:

```python
import os
from fastapi import FastAPI
from ip_safelist_middleware import IPSafeListMiddleware, ListItem, ListType

app = FastAPI()

# Different rules for different environments
if os.getenv("ENVIRONMENT") == "production":
    # Production: strict IP filtering
    list_items = [
        ListItem(path=r'^/admin/.*$', type=ListType.env),
        ListItem(path=r'^/api/.*$', type=[ListType.aws, ListType.env]),
        ListItem(path=r'^/health$', type=ListType.allow),
    ]
    networks = {"10.0.0.0/8", "172.16.0.0/12"}

elif os.getenv("ENVIRONMENT") == "staging":
    # Staging: moderate filtering
    list_items = [
        ListItem(path=r'^/(?!docs|health).*$', type=ListType.env),
    ]
    networks = {"192.168.0.0/16", "10.0.0.0/8"}

else:
    # Development: minimal filtering
    list_items = [
        ListItem(path=r'^/admin/.*$', type=ListType.env),
        ListItem(path=r'^/.*$', type=ListType.allow),  # Allow everything else
    ]
    networks = {"127.0.0.1", "192.168.0.0/16"}

app.add_middleware(
    IPSafeListMiddleware,
    list_items=list_items,
    networks=networks,
    aws_enabled=os.getenv("ENVIRONMENT") == "production",
    aws_regions=["us-east-1"] if os.getenv("ENVIRONMENT") == "production" else []
)
```

## Microservices Architecture

Service-to-service communication in a microservices setup:

```python
# User Service
app.add_middleware(
    IPSafeListMiddleware,
    list_items=[
        # Public user registration/login
        ListItem(path=r'^/api/auth/.*$', type=ListType.allow),

        # Internal service calls (from other microservices)
        ListItem(path=r'^/api/internal/.*$', type=ListType.aws),

        # Admin operations
        ListItem(path=r'^/api/admin/.*$', type=ListType.env),

        # Public user profile (with rate limiting elsewhere)
        ListItem(path=r'^/api/users/profile/.*$', type=ListType.allow),
    ]
)
```

```python
# Order Service
app.add_middleware(
    IPSafeListMiddleware,
    list_items=[
        # Only internal services can access orders
        ListItem(path=r'^/api/orders/.*$', type=ListType.aws),

        # Health checks for load balancer
        ListItem(path=r'^/health$', type=ListType.allow),

        # Metrics for monitoring
        ListItem(path=r'^/metrics$', type=ListType.env),
    ]
)
```

## Load Balancer Integration

Working with load balancers and reverse proxies:

```python
from fastapi import FastAPI, Request
from ip_safelist_middleware import IPSafeListMiddleware, ListItem, ListType

app = FastAPI()

@app.middleware("http")
async def get_real_ip(request: Request, call_next):
    """Extract real IP from load balancer headers"""
    real_ip = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
    if real_ip:
        # Modify the request to use the real IP
        request.scope["client"] = (real_ip, 0)
    response = await call_next(request)
    return response

# Apply IP filtering after real IP extraction
app.add_middleware(
    IPSafeListMiddleware,
    list_items=[
        # Health checks from load balancer (known IPs)
        ListItem(path=r'^/health$', type=ListType.env),

        # Admin from office networks
        ListItem(path=r'^/admin/.*$', type=ListType.env),

        # API from approved sources
        ListItem(path=r'^/api/.*$', type=ListType.env),
    ]
)
```

Environment configuration:
```bash
# Include load balancer IPs and approved client IPs
export IP_SAFELIST_NETWORKS="10.0.1.100,10.0.1.101,192.168.0.0/24,203.0.113.0/24"
```

## Custom Error Responses

Provide helpful error responses for blocked requests:

```python
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from ip_safelist_middleware import IPSafeListMiddleware, ListItem, ListType

app = FastAPI()

app.add_middleware(
    IPSafeListMiddleware,
    list_items=[
        ListItem(path=r'^/api/.*$', type=ListType.env),
    ],
    status_code=403,
    status_message="Access denied: Your IP address is not authorized"
)

@app.exception_handler(403)
async def forbidden_handler(request: Request, exc: HTTPException):
    """Custom 403 error response"""
    client_ip = request.client.host if request.client else "Unknown"

    return JSONResponse(
        status_code=403,
        content={
            "error": "Forbidden",
            "message": "Access denied: Your IP address is not authorized",
            "client_ip": client_ip,
            "timestamp": "2024-01-01T00:00:00Z",
            "help": "Contact support if you believe this is an error"
        }
    )
```

## Testing Configuration

Example test setup to verify IP filtering works correctly:

```python
# test_ip_filtering.py
import pytest
from fastapi.testclient import TestClient
from your_app import app

def test_allowed_ip():
    """Test that allowed IPs can access protected endpoints"""
    with TestClient(app) as client:
        # Simulate request from allowed IP
        client.client = ("192.168.1.100", 50000)
        response = client.get("/api/data")
        assert response.status_code == 200

def test_blocked_ip():
    """Test that blocked IPs cannot access protected endpoints"""
    with TestClient(app) as client:
        # Simulate request from blocked IP
        client.client = ("203.0.113.1", 50000)
        response = client.get("/api/data")
        assert response.status_code == 403

def test_public_endpoint():
    """Test that public endpoints are always accessible"""
    with TestClient(app) as client:
        # Any IP should be able to access public endpoints
        client.client = ("203.0.113.1", 50000)
        response = client.get("/health")
        assert response.status_code == 200
```

## Container Deployment

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'
services:
  api:
    build: .
    environment:
      - IP_SAFELIST_NETWORKS=10.0.0.0/8,172.16.0.0/12
      - IP_SAFELIST_AWS_ENABLED=true
      - IP_SAFELIST_AWS_REGIONS=us-east-1,us-west-2
      - IP_SAFELIST_STATUS_CODE=401
    ports:
      - "8000:8000"
    networks:
      - app_network

networks:
  app_network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

### Kubernetes Deployment

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-server
spec:
  replicas: 3
  selector:
    matchLabels:
      app: api-server
  template:
    metadata:
      labels:
        app: api-server
    spec:
      containers:
      - name: api
        image: your-api:latest
        env:
        - name: IP_SAFELIST_NETWORKS
          valueFrom:
            configMapKeyRef:
              name: ip-config
              key: allowed-networks
        - name: IP_SAFELIST_AWS_ENABLED
          value: "true"
        - name: IP_SAFELIST_AWS_REGIONS
          value: "us-west-2"
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: ip-config
data:
  allowed-networks: "10.244.0.0/16,10.96.0.0/12"
```
