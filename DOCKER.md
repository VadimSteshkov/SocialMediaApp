# Docker Documentation

Complete guide to building, running, and managing the Social Media Application using Docker and Docker Compose.

## Overview

This application uses a microservices architecture with multiple Docker containers:
- **API Service**: FastAPI REST API server
- **Database**: PostgreSQL 15 database
- **RabbitMQ**: Message queue for asynchronous processing
- **Image Resize Service**: Image processing microservice
- **Sentiment Analysis Service**: ML-based sentiment analysis
- **Text Generation Service**: GPT-2 text generation
- **Translation Service**: Multi-language translation

All services are orchestrated using Docker Compose for easy deployment and management.

## Quick Start

### Start All Services

```bash
# Clone the repository
git clone https://github.com/VadimSteshkov/SocialMediaApp.git
cd SocialMediaApp

# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f
```

### Access Services

- **Web Application**: http://localhost:5001
- **API Documentation**: http://localhost:5001/docs
- **RabbitMQ Management UI**: http://localhost:15673 (guest/guest)

### Stop Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (⚠️ deletes all data)
docker-compose down -v
```

## Architecture

### Container Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Docker Network                       │
│              (social-media-network)                      │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   API        │  │  PostgreSQL  │  │   RabbitMQ   │  │
│  │  (Port 5001) │  │  (Port 5432) │  │  (Port 5672) │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │
│         │                  │                  │          │
│         └──────────────────┴──────────────────┘          │
│                          │                              │
│         ┌────────────────┴────────────────┐            │
│         │                                  │            │
│  ┌──────▼────────┐  ┌──────────────┐  ┌───▼────────┐  │
│  │ Image Resize  │  │  Sentiment   │  │   Text     │  │
│  │   Service     │  │  Analysis    │  │ Generation │  │
│  └───────────────┘  └──────────────┘  └────────────┘  │
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │         Translation Service                       │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### Service Dependencies

```
API Service
├── Depends on: Database (healthy)
├── Depends on: RabbitMQ (healthy)
└── Uses: uploads_data volume

Image Resize Service
├── Depends on: Database (healthy)
├── Depends on: RabbitMQ (healthy)
└── Uses: uploads_data volume

Sentiment Analysis Service
├── Depends on: Database (healthy)
└── Depends on: RabbitMQ (healthy)

Text Generation Service
└── Depends on: RabbitMQ (healthy)

Translation Service
└── Depends on: RabbitMQ (healthy)
```

## Services

### API Service

**Container**: `social-media-api`  
**Image**: Built from `Dockerfile`  
**Port**: `5001` (configurable via `PORT`)

**Features**:
- FastAPI REST API server
- Serves web frontend (HTML/CSS/JavaScript)
- Handles all HTTP requests
- Integrates with database and message queue

**Health Check**: `/api/health` endpoint

**Volumes**:
- `uploads_data`: Shared image storage
- `./static:/app/static:ro`: Static files (read-only)

### Database Service

**Container**: `social-media-db`  
**Image**: `postgres:15-alpine`  
**Port**: `5434:5432` (host:container)

**Features**:
- PostgreSQL 15 database
- Persistent data storage
- Health checks for readiness

**Volumes**:
- `postgres_data`: Persistent database storage

**Environment Variables**:
- `POSTGRES_DB`: Database name (default: `social_media`)
- `POSTGRES_USER`: Database user (default: `postgres`)
- `POSTGRES_PASSWORD`: Database password (default: `postgres`)

### RabbitMQ Service

**Container**: `social-media-rabbitmq`  
**Image**: `rabbitmq:3-management-alpine`  
**Ports**:
- `5672`: AMQP protocol
- `15673:15672`: Management UI

**Features**:
- Message queue for asynchronous processing
- Management UI for monitoring
- Persistent queue storage

**Volumes**:
- `rabbitmq_data`: Persistent queue storage

**Default Credentials**:
- Username: `guest`
- Password: `guest`

### Image Resize Service

**Container**: `social-media-image-resize`  
**Image**: Built from `Dockerfile.resize`  
**Port**: None (internal only)

**Features**:
- Processes image resize requests from queue
- Generates thumbnails (300x300px)
- Updates database with thumbnail paths

**Dependencies**: Pillow (PIL)

**Volumes**:
- `uploads_data`: Shared image storage

### Sentiment Analysis Service

**Container**: `social-media-sentiment-analysis`  
**Image**: Built from `Dockerfile.sentiment`  
**Port**: None (internal only)

**Features**:
- Analyzes post sentiment using RoBERTa model
- Updates database with sentiment labels and scores
- Supports POSITIVE, NEGATIVE, NEUTRAL classifications

**Model**: `cardiffnlp/twitter-roberta-base-sentiment`

**Dependencies**: transformers, torch, sentencepiece

### Text Generation Service

**Container**: `social-media-text-generation`  
**Image**: Built from `Dockerfile.textgen`  
**Port**: None (internal only)

**Features**:
- Generates text using GPT-2 model
- Responds via dedicated response queue
- Supports prompt-based and tag-based generation

**Model**: `gpt2`

**Dependencies**: transformers, torch

### Translation Service

**Container**: `social-media-translation`  
**Image**: Built from `Dockerfile.translation`  
**Port**: None (internal only)

**Features**:
- Translates text between multiple languages
- Automatic language detection
- Supports: English, Russian, German, Spanish, French
- Handles long texts with sentence-level chunking

**Models**: Helsinki-NLP MarianMT models

**Dependencies**: transformers, torch, sentencepiece

## Volumes

### Persistent Volumes

The application uses three Docker volumes for data persistence:

1. **postgres_data**
   - Stores PostgreSQL database files
   - Location: `/var/lib/postgresql/data` (container)
   - Persists across container restarts

2. **rabbitmq_data**
   - Stores RabbitMQ queue data
   - Location: `/var/lib/rabbitmq` (container)
   - Persists across container restarts

3. **uploads_data**
   - Shared storage for uploaded images
   - Location: `/app/uploads` (container)
   - Shared between API and Image Resize services
   - Contains:
     - `full/`: Full-size images
     - `thumbnails/`: Generated thumbnails

### Volume Management

```bash
# List volumes
docker volume ls

# Inspect volume
docker volume inspect socialmediaapp_postgres_data

# Remove volume (⚠️ deletes data)
docker volume rm socialmediaapp_postgres_data

# Backup volume data
docker run --rm -v socialmediaapp_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz /data
```

## Networks

### Docker Network

All services communicate via a bridge network: `social-media-network`

**Network Type**: Bridge  
**Driver**: bridge (default)

**Benefits**:
- Isolated container communication
- Automatic DNS resolution (service names as hostnames)
- No external exposure of internal services

**Service Communication**:
- API → Database: `db:5432`
- API → RabbitMQ: `rabbitmq:5672`
- Services → RabbitMQ: `rabbitmq:5672`

## Environment Variables

### Application Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `5001` | API server port |

### Database Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `DB_TYPE` | `postgresql` | Database type (postgresql/sqlite) |
| `DB_HOST` | `db` | Database hostname |
| `DB_PORT` | `5432` | Database port |
| `DB_NAME` | `social_media` | Database name |
| `DB_USER` | `postgres` | Database user |
| `DB_PASSWORD` | `postgres` | Database password |

### RabbitMQ Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `RABBITMQ_HOST` | `rabbitmq` | RabbitMQ hostname |
| `RABBITMQ_PORT` | `5672` | RabbitMQ AMQP port |
| `RABBITMQ_USER` | `guest` | RabbitMQ username |
| `RABBITMQ_PASSWORD` | `guest` | RabbitMQ password |

### Setting Environment Variables

**Option 1: Environment file (`.env`)**
```bash
# Create .env file
cat > .env << EOF
DB_PASSWORD=my_secure_password
RABBITMQ_PASSWORD=my_rabbitmq_password
PORT=5001
EOF

# Start services
docker-compose up -d
```

**Option 2: Export before running**
```bash
export DB_PASSWORD=my_secure_password
export RABBITMQ_PASSWORD=my_rabbitmq_password
docker-compose up -d
```

**Option 3: Inline with docker-compose**
```bash
DB_PASSWORD=my_password docker-compose up -d
```

## Common Commands

### Service Management

```bash
# Start all services
docker-compose up -d

# Start specific service
docker-compose up -d api

# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v

# Restart service
docker-compose restart api

# View service status
docker-compose ps

# View service logs
docker-compose logs -f api
docker-compose logs -f sentiment-analysis
docker-compose logs -f text-generation
docker-compose logs -f translation
```

### Building Images

```bash
# Build all images
docker-compose build

# Build specific service
docker-compose build api

# Build without cache
docker-compose build --no-cache

# Rebuild and restart
docker-compose up -d --build
```

### Database Operations

```bash
# Access PostgreSQL shell
docker-compose exec db psql -U postgres -d social_media

# Backup database
docker-compose exec db pg_dump -U postgres social_media > backup.sql

# Restore database
docker-compose exec -T db psql -U postgres social_media < backup.sql

# View database logs
docker-compose logs -f db
```

### RabbitMQ Operations

```bash
# Access RabbitMQ Management UI
open http://localhost:15673
# Login: guest / guest

# List queues (via container)
docker-compose exec rabbitmq rabbitmqctl list_queues

# View RabbitMQ logs
docker-compose logs -f rabbitmq
```

### Container Inspection

```bash
# Execute command in container
docker-compose exec api python --version

# Access container shell
docker-compose exec api /bin/bash

# View container resource usage
docker stats

# Inspect container configuration
docker-compose config
```

## Health Checks

All services include health checks to ensure proper startup order and reliability.

### API Service Health Check

- **Endpoint**: `http://localhost:5001/api/health`
- **Interval**: 30 seconds
- **Timeout**: 10 seconds
- **Retries**: 3
- **Start Period**: 10 seconds

### Database Health Check

- **Command**: `pg_isready -U postgres`
- **Interval**: 10 seconds
- **Timeout**: 5 seconds
- **Retries**: 5

### RabbitMQ Health Check

- **Command**: `rabbitmq-diagnostics ping`
- **Interval**: 10 seconds
- **Timeout**: 5 seconds
- **Retries**: 5

### Dependency Management

Services wait for dependencies to be healthy before starting:
- API waits for Database and RabbitMQ
- Image Resize waits for Database and RabbitMQ
- Sentiment Analysis waits for Database and RabbitMQ
- Text Generation waits for RabbitMQ
- Translation waits for RabbitMQ

## Troubleshooting

### Services Not Starting

**Problem**: Container fails to start

**Solutions**:
```bash
# Check logs
docker-compose logs api

# Check service status
docker-compose ps

# Verify dependencies are healthy
docker-compose ps db rabbitmq

# Restart service
docker-compose restart api
```

### Database Connection Issues

**Problem**: API cannot connect to database

**Solutions**:
```bash
# Verify database is running
docker-compose ps db

# Check database logs
docker-compose logs db

# Test connection from API container
docker-compose exec api python -c "from database import Database; db = Database(); print('Connected!')"

# Verify environment variables
docker-compose exec api env | grep DB_
```

### RabbitMQ Connection Issues

**Problem**: Services cannot connect to RabbitMQ

**Solutions**:
```bash
# Verify RabbitMQ is running
docker-compose ps rabbitmq

# Check RabbitMQ logs
docker-compose logs rabbitmq

# Access RabbitMQ Management UI
open http://localhost:15673

# Verify queues exist
docker-compose exec rabbitmq rabbitmqctl list_queues

# Check network connectivity
docker-compose exec api ping rabbitmq
```

### Image Processing Not Working

**Problem**: Images not being resized

**Solutions**:
```bash
# Check Image Resize service logs
docker-compose logs -f image-resize

# Verify RabbitMQ queue
docker-compose exec rabbitmq rabbitmqctl list_queues | grep image

# Check uploads volume
docker-compose exec api ls -la /app/uploads

# Verify service is running
docker-compose ps image-resize
```

### ML Services Not Working

**Problem**: Sentiment/Text Generation/Translation not working

**Solutions**:
```bash
# Check service logs (models download on first run - may take 5-10 minutes)
docker-compose logs -f sentiment-analysis
docker-compose logs -f text-generation
docker-compose logs -f translation

# Verify models are loading
docker-compose logs sentiment-analysis | grep "Loading model"
docker-compose logs text-generation | grep "Loading model"
docker-compose logs translation | grep "Loading model"

# Check service is running
docker-compose ps sentiment-analysis text-generation translation

# Verify RabbitMQ connection
docker-compose exec sentiment-analysis python -c "import pika; print('RabbitMQ available')"
```

### Port Conflicts

**Problem**: Port already in use

**Solutions**:
```bash
# Check what's using the port
lsof -i :5001
lsof -i :5434
lsof -i :5672
lsof -i :15673

# Change port in docker-compose.yml or .env
# Example: PORT=5002 docker-compose up -d
```

### Volume Issues

**Problem**: Data not persisting or volume errors

**Solutions**:
```bash
# List volumes
docker volume ls

# Inspect volume
docker volume inspect socialmediaapp_postgres_data

# Remove and recreate volume (⚠️ deletes data)
docker-compose down -v
docker-compose up -d

# Check volume mount points
docker-compose config | grep -A 5 volumes
```

### Network Issues

**Problem**: Services cannot communicate

**Solutions**:
```bash
# List networks
docker network ls

# Inspect network
docker network inspect socialmediaapp_social-media-network

# Verify services are on same network
docker-compose config | grep networks

# Test connectivity
docker-compose exec api ping db
docker-compose exec api ping rabbitmq
```

## Production Deployment

### Security Considerations

1. **Change Default Passwords**:
   ```bash
   # Use strong passwords in .env
   DB_PASSWORD=strong_random_password
   RABBITMQ_PASSWORD=strong_random_password
   ```

2. **Limit Port Exposure**:
   - Only expose necessary ports
   - Use reverse proxy (nginx) for API
   - Don't expose database port externally

3. **Use Production Images**:
   - Build optimized images
   - Use multi-stage builds
   - Minimize image size

4. **Enable SSL/TLS**:
   - Use HTTPS for API
   - Secure RabbitMQ connections
   - Encrypt database connections

### Production Configuration

```yaml
# docker-compose.prod.yml example
version: '3.8'
services:
  api:
    restart: always
    environment:
      - DB_PASSWORD=${DB_PASSWORD}
      - RABBITMQ_PASSWORD=${RABBITMQ_PASSWORD}
    # Add resource limits
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G
```

### Monitoring

```bash
# Monitor resource usage
docker stats

# Monitor logs
docker-compose logs -f

# Set up log aggregation
# Use ELK stack, Loki, or similar
```

## Backup and Restore

### Database Backup

```bash
# Create backup
docker-compose exec db pg_dump -U postgres social_media > backup_$(date +%Y%m%d).sql

# Automated backup script
cat > backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="./backups"
mkdir -p $BACKUP_DIR
docker-compose exec -T db pg_dump -U postgres social_media > $BACKUP_DIR/backup_$(date +%Y%m%d_%H%M%S).sql
EOF
chmod +x backup.sh
```

### Database Restore

```bash
# Restore from backup
docker-compose exec -T db psql -U postgres social_media < backup.sql
```

### Volume Backup

```bash
# Backup PostgreSQL volume
docker run --rm -v socialmediaapp_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_volume_$(date +%Y%m%d).tar.gz /data

# Restore PostgreSQL volume
docker run --rm -v socialmediaapp_postgres_data:/data -v $(pwd):/backup alpine tar xzf /backup/postgres_volume_YYYYMMDD.tar.gz -C /
```

## Performance Optimization

### Resource Limits

Add to `docker-compose.yml`:
```yaml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
```

### Model Caching

ML services cache models in memory. First request may be slow (model download), subsequent requests are faster.

### Database Optimization

- Use connection pooling (already implemented)
- Add indexes for frequently queried columns
- Regular VACUUM and ANALYZE

### RabbitMQ Optimization

- Configure queue durability
- Set appropriate message TTL
- Monitor queue lengths

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [RabbitMQ Documentation](https://www.rabbitmq.com/documentation.html)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

---

For more information about the application, see [README.md](README.md).
