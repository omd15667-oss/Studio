# Quick Test - DSM API

```bash
# 1. Register
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "SecurePass123!"
  }'

# 2. Login
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "SecurePass123!"
  }' | jq -r '.access_token')

echo "Token: $TOKEN"

# 3. Create Note
curl -X POST http://localhost:8000/api/v1/notes \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My First Note",
    "content": "This is encrypted and secure!"
  }'

# 4. List Notes
curl -X GET http://localhost:8000/api/v1/notes \
  -H "Authorization: Bearer $TOKEN"

# 5. Get Audit Logs
curl -X GET http://localhost:8000/api/v1/audit/logs \
  -H "Authorization: Bearer $TOKEN"
```