# Digital Sovereignty Mirror - API Endpoints Reference

## Base URL
```
http://localhost:8000
```

## Authentication Endpoints

### Register
```
POST /api/v1/auth/register

Request:
{
  "username": "yourname",
  "email": "you@example.com",
  "password": "SecurePassword123!"
}

Response:
{
  "id": 1,
  "username": "yourname",
  "email": "you@example.com",
  "created_at": "2024-01-01T00:00:00"
}
```

### Login
```
POST /api/v1/auth/login

Request:
{
  "username": "yourname",
  "password": "SecurePassword123!"
}

Response:
{
  "access_token": "eyJhbGciOi...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

## Notes Endpoints (Require Auth)

### Create Note
```
POST /api/v1/notes
Header: Authorization: Bearer <token>

Request:
{
  "title": "Note Title",
  "content": "Note content here"
}

Response:
{
  "id": 1,
  "title": "Note Title",
  "content": "Note content here",
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T00:00:00"
}
```

### List Notes
```
GET /api/v1/notes
Header: Authorization: Bearer <token>

Response:
[
  {
    "id": 1,
    "title": "Note 1",
    "content": "...",
    "created_at": "2024-01-01T00:00:00",
    "updated_at": "2024-01-01T00:00:00"
  }
]
```

### Get Note
```
GET /api/v1/notes/{note_id}
Header: Authorization: Bearer <token>
```

### Update Note
```
PUT /api/v1/notes/{note_id}
Header: Authorization: Bearer <token>

Request:
{
  "title": "Updated Title",
  "content": "Updated content"
}
```

### Delete Note
```
DELETE /api/v1/notes/{note_id}
Header: Authorization: Bearer <token>

Response:
{
  "message": "Note deleted successfully"
}
```

## Privacy & Audit

### Get Audit Logs
```
GET /api/v1/audit/logs
Header: Authorization: Bearer <token>

Response:
{
  "user_id": 1,
  "logs": [
    {
      "timestamp": "2024-01-01T00:00:00",
      "user_id": 1,
      "action": "create_note",
      "resource_type": "note",
      "resource_id": 1,
      "details": {}
    }
  ],
  "total": 5
}
```

## System Endpoints

### Health Check
```
GET /health

Response:
{
  "status": "healthy",
  "service": "Digital Sovereignty Mirror API",
  "version": "0.1.0",
  "timestamp": "2024-01-01T00:00:00"
}
```

### API Info
```
GET /

Response:
{
  "name": "Digital Sovereignty Mirror",
  "version": "0.1.0",
  "mission": "Your Data. Your Knowledge. Your Decision."
}
```

## Documentation

- **Interactive Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json