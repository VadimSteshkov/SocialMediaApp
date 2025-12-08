# Docker Container Orchestration

This document describes how to build and run the Social Media App using Docker Compose with separate containers for the REST API and PostgreSQL database.

## Architecture

The application uses a multi-container setup:
- **API Container**: FastAPI REST API server
- **Database Container**: PostgreSQL 15 database
- **Persistent Volumes**: Data persists across container restarts
- **Network**: Containers communicate via Docker network

## Quick Start

### Using Docker Compose (Recommended)

#### Development Environment
```bash
# Copy environment file
cp .env.example .env.dev

# Start services
docker-compose -f docker-compose.yml -f docker-compose.dev.yml --env-file .env.dev up
```

#### Production Environment
```bash
# Copy and configure production environment file
cp .env.example .env.prod
# Edit .env.prod with production credentials

# Start services
docker-compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.prod up -d
```

#### Default (using docker-compose.yml only)
```bash
docker-compose up
```

### Build and Run Individual Containers

#### Build the API container
```bash
docker build -t social-media-api .
```

#### Run with PostgreSQL
The API container requires a PostgreSQL database. Use docker-compose for the full setup.

## Container Details

### API Container
- **Image**: Built from `Dockerfile`
- **Port**: `5001` (configurable via `PORT` environment variable)
- **Health Check**: `/api/health` endpoint
- **Dependencies**: Waits for database to be healthy before starting

### Database Container
- **Image**: `postgres:15-alpine`
- **Port**: `5432` (configurable via `DB_PORT` environment variable)
- **Volume**: `postgres_data` - persistent storage for database files
- **Health Check**: PostgreSQL readiness check

### Volumes
- `postgres_data`: Persistent storage for PostgreSQL data
  - Data survives container restarts and recreations
  - Located at `/var/lib/postgresql/data` in the container

### Networks
- `social-media-network`: Bridge network for container communication

## Configuration

### Environment Variables

#### Application Configuration
- `PORT`: API server port (default: `5001`)

#### Database Configuration
- `DB_TYPE`: Database type - `postgresql` or `sqlite` (default: `postgresql` when `DB_HOST` is set)
- `DB_HOST`: Database hostname (default: `db` for docker-compose)
- `DB_PORT`: Database port (default: `5432`)
- `DB_NAME`: Database name (default: `social_media`)
- `DB_USER`: Database user (default: `postgres`)
- `DB_PASSWORD`: Database password (default: `postgres`)

#### SQLite Fallback
If `DB_HOST` is not set, the application falls back to SQLite:
- `DB_PATH`: SQLite database file path (default: `social_media.db`)

### Environment Files

- `.env.example`: Example configuration file
- `.env.dev`: Development environment configuration
- `.env.prod`: Production environment configuration (not in git)

### Docker Compose Override Files

- `docker-compose.yml`: Base configuration
- `docker-compose.dev.yml`: Development overrides (exposes DB port, mounts source code)
- `docker-compose.prod.yml`: Production overrides (hides DB port, production optimizations)

## Data Persistence

### PostgreSQL Data
PostgreSQL data is stored in a Docker volume named `postgres_data`. This ensures:
- Data persists when containers are stopped
- Data persists when containers are recreated
- Data can be backed up and restored

### Backup and Restore

#### Backup PostgreSQL data
```bash
docker-compose exec db pg_dump -U postgres social_media > backup.sql
```

#### Restore PostgreSQL data
```bash
docker-compose exec -T db psql -U postgres social_media < backup.sql
```

## Common Commands

### Start services
```bash
docker-compose up -d
```

### Stop services
```bash
docker-compose down
```

### View logs
```bash
docker-compose logs -f api
docker-compose logs -f db
```

### Access database
```bash
docker-compose exec db psql -U postgres -d social_media
```

### Rebuild containers
```bash
docker-compose build
docker-compose up -d
```

### Remove volumes (⚠️ deletes all data)
```bash
docker-compose down -v
```

## Health Checks

Both containers include health checks:
- **API**: Checks `/api/health` endpoint
- **Database**: Checks PostgreSQL readiness with `pg_isready`

The API container waits for the database to be healthy before starting.

## Development vs Production

### Development
- Database port exposed for local tools (pgAdmin, etc.)
- Source code mounted as volume for hot reload
- Development credentials in `.env.dev`

### Production
- Database port not exposed (only accessible via Docker network)
- Optimized container configuration
- Production credentials in `.env.prod` (not in git)

## Troubleshooting

### Database connection issues
1. Check if database container is running: `docker-compose ps`
2. Check database logs: `docker-compose logs db`
3. Verify environment variables: `docker-compose config`

### API not starting
1. Check if database is healthy: `docker-compose ps`
2. Check API logs: `docker-compose logs api`
3. Verify network connectivity: Containers must be on the same network

### Data not persisting
1. Verify volume exists: `docker volume ls | grep postgres_data`
2. Check volume mount: `docker-compose config | grep -A 5 volumes`
