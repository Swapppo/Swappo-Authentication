# Swappo-Auth

Authentication microservice for the Swappo platform with JWT-based authentication, user management, and profile features.

## Features

- User registration and login with JWT tokens (access + refresh)
- Password management (change password)
- User profile management with shipping address
- Prometheus metrics integration
- PostgreSQL support with fallback to in-memory storage
- CORS-enabled for mobile applications

## Quick Start

### Docker (Recommended)

```bash
docker-compose up --build
```

Or on Windows:
```powershell
.\start-docker.ps1
```

### Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the server:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

> **Note**: Set `DATABASE_URL` environment variable to use PostgreSQL, otherwise in-memory storage is used.

## API Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/` | API information | No |
| GET | `/health` | Health check | No |
| POST | `/api/v1/auth/register` | Register new user | No |
| POST | `/api/v1/auth/login` | Login and get tokens | No |
| POST | `/api/v1/auth/refresh` | Refresh access token | No |
| GET | `/api/v1/auth/me` | Get current user info | Yes |
| POST | `/api/v1/auth/change-password` | Change password | Yes |
| PUT | `/api/v1/auth/profile` | Update user profile | Yes |
| GET | `/metrics` | Prometheus metrics | No |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | None | PostgreSQL connection string |
| `SECRET_KEY` | Auto-generated | JWT access token secret |
| `REFRESH_SECRET_KEY` | Auto-generated | JWT refresh token secret |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 30 | Access token expiration |
| `REFRESH_TOKEN_EXPIRE_DAYS` | 7 | Refresh token expiration |

## Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Testing

```bash
pytest tests/test_auth.py -v
```

## Generate API Schema

```bash
python -c "import json; from app.main import app; print(json.dumps(app.openapi(), indent=2))" > api_schema.json
```
