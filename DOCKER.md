# Docker Container for REST API

This document describes how to build and run the Social Media App REST API as a Docker container.

## Quick Start

### Build the container
```bash
docker build -t social-media-api .
```

### Run the container
```bash
docker run -p 5001:5001 social-media-api
```

### Using Docker Compose
```bash
docker-compose up
```

## Container Details

### What's included
- FastAPI REST API server
- All Python dependencies
- Static files (HTML, CSS, JS) - served by FastAPI
- SQLite database (created automatically)

### Port
- Default: `5001`
- Configurable via `PORT` environment variable

### Database
- SQLite database file: `/app/data/social_media.db` (inside container)
- For persistence, mount a volume: `-v ./data:/app/data`

### Health Check
The container includes a health check endpoint at `/api/health`

## Environment Variables

- `PORT`: Server port (default: 5001)
- `DB_PATH`: Database file path (default: `social_media.db`)

## GitHub Container Registry

The container is automatically built and pushed to GitHub Container Registry (ghcr.io) via GitHub Actions.

Image location: `ghcr.io/vadimsteshkov/socialmediaapp`

