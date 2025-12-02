# FlowForward Finance

A microservices platform built with FastAPI, SQLAlchemy, and PostgreSQL, managed as a Pants monorepo.

## Prerequisites

- Python 3.12+
- Docker & Docker Compose
- [Pants](https://www.pantsbuild.org/) (optional, for build system)

## Getting Started

### Quick Start with Docker

```bash 
# Start all services (databases + APIs)
docker compose up --build

# Or run in background
docker compose up --build -d
```

Services will be available at:
- **Auth Service**: http://localhost:8000
- **Auth API Docs**: http://localhost:8000/docs

### Local Development

```bash
# Start databases only
docker compose up postgres-auth -d

# Install dependencies for a service
cd services/auth
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start the service
uvicorn main:app --reload --port 8000
```

### Using Pants Build System

```bash
# Generate dependency lockfiles (first time only)
pants generate-lockfiles

# Run the auth service
pants run services/auth:auth-server

# Format code
pants fmt ::

# Lint code
pants lint ::

# Type check
pants check ::

# Run tests
pants test ::

# Package as executable
pants package services/auth:auth-server
```

## Project Structure

```
flowforward-finance/
├── pants.toml              # Pants build configuration
├── pyproject.toml          # Python tooling config (black, isort, mypy)
├── docker-compose.yml      # Root compose (includes all services)
├── services/
│   └── auth/               # Authentication microservice
│       ├── README.md       # Service documentation
│       ├── docker-compose.yml
│       ├── Dockerfile
│       └── ...
└── shared/                 # Shared libraries (future)
```

## Services

| Service | Port | Description |
|---------|------|-------------|
| auth | 8000 | Authentication & JWT tokens |

## Environment Configuration

Copy the example environment file and configure:

```bash
cp .env.example .env
```

Key variables:
- `AUTH_DB_*` - Database connection settings
- `AUTH_JWT_SECRET_KEY` - JWT signing secret (generate with `openssl rand -hex 32`)

## Adding a New Service

1. Create service directory: `services/<name>/`
2. Add `docker-compose.yml` with dedicated database
3. Add `BUILD` file for Pants
4. Include in root `docker-compose.yml`

See `services/auth/` as a reference implementation.