# Auth Service

Authentication microservice for FlowForward Finance platform using FastAPI, SQLAlchemy, and PostgreSQL.

## Features

- User registration and authentication
- JWT access tokens (short-lived)
- JWT refresh tokens with rotation (long-lived)
- Token revocation and logout
- Password hashing with bcrypt

## Quick Start

### Using Docker Compose (Recommended)

From the project root:

```bash
docker compose up --build
```

This starts:
- PostgreSQL database on port 5432
- Auth service on port 8000

### Local Development

```bash
# Start only the database
docker compose up postgres-auth -d

# Install dependencies
cd services/auth
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start the server
uvicorn main:app --reload --port 8000
```

## API Endpoints

### Health & Info

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Service info |
| GET | `/health` | Health check |
| GET | `/docs` | Swagger UI documentation |
| GET | `/redoc` | ReDoc documentation |

### Authentication

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/v1/auth/register` | Register new user | No |
| POST | `/api/v1/auth/login` | Login (OAuth2 form) | No |
| POST | `/api/v1/auth/login/json` | Login (JSON body) | No |
| POST | `/api/v1/auth/refresh` | Refresh access token | No |
| POST | `/api/v1/auth/logout` | Logout (revoke token) | Yes |
| POST | `/api/v1/auth/logout/all` | Logout all devices | Yes |
| GET | `/api/v1/auth/me` | Get current user | Yes |

## Request/Response Examples

### Register User

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "johndoe",
    "password": "securepassword123"
  }'
```

Response:
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "username": "johndoe",
  "is_active": true,
  "is_superuser": false,
  "created_at": "2024-12-02T00:00:00Z",
  "updated_at": "2024-12-02T00:00:00Z"
}
```

### Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=johndoe&password=securepassword123"
```

Response:
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

### Access Protected Endpoint

```bash
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer <access_token>"
```

### Refresh Token

```bash
curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "<refresh_token>"}'
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `AUTH_DB_USER` | auth_user | Database username |
| `AUTH_DB_PASSWORD` | auth_password | Database password |
| `AUTH_DB_NAME` | auth_db | Database name |
| `AUTH_DB_HOST` | localhost | Database host |
| `AUTH_DB_PORT` | 5432 | Database port |
| `AUTH_JWT_SECRET_KEY` | (change me) | JWT signing secret |
| `AUTH_JWT_ALGORITHM` | HS256 | JWT algorithm |
| `AUTH_ACCESS_TOKEN_EXPIRE_MINUTES` | 30 | Access token TTL |
| `AUTH_REFRESH_TOKEN_EXPIRE_DAYS` | 7 | Refresh token TTL |
| `DEBUG` | false | Enable debug mode |

## Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```

## Project Structure

```
services/auth/
├── main.py           # FastAPI application entry point
├── config.py         # Pydantic Settings configuration
├── database.py       # SQLAlchemy engine and session
├── models.py         # SQLAlchemy models (User, RefreshToken)
├── schemas.py        # Pydantic request/response schemas
├── auth.py           # Authentication routes and JWT logic
├── dependencies.py   # FastAPI dependencies
├── Dockerfile        # Container image definition
├── docker-compose.yml # Service and database configuration
├── requirements.txt  # Python dependencies
├── alembic.ini       # Alembic configuration
└── alembic/          # Database migrations
    └── versions/
```

