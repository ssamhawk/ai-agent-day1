# REST API Design Best Practices

## What is REST?

REST (Representational State Transfer) is an architectural style for designing networked applications. A RESTful API uses HTTP requests to access and manipulate data.

## HTTP Methods

### GET
Retrieve data from the server. Should be idempotent (multiple identical requests have the same effect).
```
GET /api/users          # Get all users
GET /api/users/123      # Get user with ID 123
```

### POST
Create a new resource on the server.
```
POST /api/users
Body: {"name": "John", "email": "john@example.com"}
```

### PUT
Update an existing resource (replace entire resource).
```
PUT /api/users/123
Body: {"name": "John Updated", "email": "john@example.com"}
```

### PATCH
Partially update a resource.
```
PATCH /api/users/123
Body: {"email": "newemail@example.com"}
```

### DELETE
Remove a resource from the server.
```
DELETE /api/users/123
```

## URL Design Principles

### Use Nouns, Not Verbs
- ✅ Good: `/api/users`
- ❌ Bad: `/api/getUsers`

### Use Plural Nouns for Collections
- ✅ Good: `/api/users`
- ❌ Bad: `/api/user`

### Nested Resources
```
GET /api/users/123/orders        # Get orders for user 123
POST /api/users/123/orders       # Create order for user 123
GET /api/users/123/orders/456    # Get specific order
```

## HTTP Status Codes

### Success Codes
- **200 OK**: Request succeeded
- **201 Created**: Resource created successfully
- **204 No Content**: Request succeeded, no content to return

### Client Error Codes
- **400 Bad Request**: Invalid request syntax
- **401 Unauthorized**: Authentication required
- **403 Forbidden**: No permission to access
- **404 Not Found**: Resource not found
- **422 Unprocessable Entity**: Validation error

### Server Error Codes
- **500 Internal Server Error**: Generic server error
- **503 Service Unavailable**: Server temporarily unavailable

## API Versioning

Include version in URL:
```
https://api.example.com/v1/users
https://api.example.com/v2/users
```

## Pagination

For large collections:
```
GET /api/users?page=2&limit=20
```

Response should include metadata:
```json
{
  "data": [...],
  "pagination": {
    "page": 2,
    "limit": 20,
    "total": 100,
    "total_pages": 5
  }
}
```

## Error Response Format

Consistent error format:
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid email format",
    "details": [
      {
        "field": "email",
        "issue": "Must be a valid email address"
      }
    ]
  }
}
```

## Authentication

Common methods:
- **API Keys**: Simple but less secure
- **OAuth 2.0**: Industry standard for authorization
- **JWT (JSON Web Tokens)**: Stateless authentication

Example JWT header:
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```
