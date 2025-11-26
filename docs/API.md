# API Documentation

## Base URL

```
http://localhost:8000
```

## Health Check Endpoints

### Get Health Status

Check the health status of the API and database connection.

**Endpoint:** `GET /health`

**Response:**

```json
{
  "status": "healthy",
  "app_name": "WHMCS Stock Monitor",
  "version": "1.0.0",
  "database": "connected"
}
```

**Status Codes:**
- `200 OK`: Service is healthy
- `503 Service Unavailable`: Database connection failed

### Root Endpoint

Get API information and available endpoints.

**Endpoint:** `GET /`

**Response:**

```json
{
  "message": "Welcome to WHMCS Stock Monitor",
  "version": "1.0.0",
  "docs": "/docs",
  "health": "/health"
}
```

## Interactive Documentation

### Swagger UI

Access interactive API documentation with testing capabilities:

```
http://localhost:8000/docs
```

### ReDoc

Access alternative API documentation:

```
http://localhost:8000/redoc
```

### OpenAPI Schema

Download the OpenAPI JSON schema:

```
http://localhost:8000/openapi.json
```

## Future Endpoints

The following endpoints will be implemented in future iterations:

### Monitor Configuration

- `GET /api/v1/monitors` - List all monitor configurations
- `POST /api/v1/monitors` - Create a new monitor configuration
- `GET /api/v1/monitors/{id}` - Get a specific monitor configuration
- `PUT /api/v1/monitors/{id}` - Update a monitor configuration
- `DELETE /api/v1/monitors/{id}` - Delete a monitor configuration

### Stock Records

- `GET /api/v1/monitors/{id}/stock-records` - Get stock history for a monitor
- `GET /api/v1/stock-records` - List all stock records
- `GET /api/v1/stock-records/{id}` - Get a specific stock record

### Notifications

- `GET /api/v1/notifications` - List all notifications
- `GET /api/v1/notifications/{id}` - Get a specific notification
- `POST /api/v1/notifications/{id}/retry` - Retry a failed notification

### Statistics

- `GET /api/v1/stats/overview` - Get overview statistics
- `GET /api/v1/stats/monitors/{id}` - Get statistics for a specific monitor

## Error Responses

All endpoints may return the following error responses:

### 400 Bad Request

```json
{
  "detail": "Invalid request parameters"
}
```

### 404 Not Found

```json
{
  "detail": "Resource not found"
}
```

### 500 Internal Server Error

```json
{
  "detail": "Internal server error"
}
```

### 503 Service Unavailable

```json
{
  "detail": "Service temporarily unavailable"
}
```

## Authentication

Authentication will be implemented in future iterations. Possible approaches:

- API Key authentication
- JWT tokens
- OAuth2

## Rate Limiting

Rate limiting will be implemented in future iterations to prevent abuse.

## CORS

CORS is currently configured to allow all origins for development. This should be restricted in production.

## Versioning

The API uses URL versioning (e.g., `/api/v1/`). The current implementation is version 1.0.0.
