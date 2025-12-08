# SocialMediaApp

Simple social media app for the Software Engineering course. This application stores social media posts in a SQLite database with support for images, text comments, and user information.

## Features

- Store social media posts with image, text, and user information
- Retrieve the latest post from the database
- REST API built with FastAPI
- Web frontend (HTML/CSS/JavaScript)
- Automatic OpenAPI specification generation
- Comprehensive test suite
- GitHub Actions CI/CD for automated testing on pull requests

## Project Structure

```
SocialMediaApp/
├── api.py              # FastAPI REST API server
├── app.py              # Main application with sample posts
├── database.py         # Database operations and schema
├── test_app.py         # Database tests
├── test_api.py         # REST API tests
├── test_social_features.py  # Social features tests
├── requirements.txt    # Python dependencies
├── Dockerfile          # Docker container definition
├── docker-compose.yml  # Docker Compose configuration
├── .dockerignore       # Files to exclude from Docker build
├── DOCKER.md           # Docker documentation
├── openapi.json        # OpenAPI specification (auto-generated)
├── static/             # Web frontend files
│   ├── index.html      # Main HTML page
│   ├── style.css       # Styles
│   ├── app.js          # JavaScript client
│   └── icons/
│       └── logo.png    # Application logo
└── .github/
    └── workflows/
        ├── test.yml              # Test workflow
        └── docker-build.yml      # Docker build workflow
```

## Requirements

- Python 3.11 or higher
- FastAPI and Uvicorn (see requirements.txt)

## Usage

### Option 1: Run Locally (Without Docker)

#### Installation

```bash
pip install -r requirements.txt
```

#### Running the REST API Server

```bash
python api.py
```

The server will start on `http://localhost:5001` (or port specified by `PORT` environment variable).

### Option 2: Run with Docker (Recommended for Deployment)

#### Quick Start with Docker Compose

1. Navigate to the project directory:
```bash
cd SocialMediaApp
```

2. Start the containers:
```bash
docker-compose up -d
```

3. Check container status:
```bash
docker-compose ps
```

4. Verify the API is working:
```bash
curl http://localhost:5001/api/health
```

#### Using Docker Compose (Easiest)

```bash
# Build and start the container
docker-compose up

# Or run in background
docker-compose up -d

# Stop the container
docker-compose down
```

#### Using Docker directly

```bash
# Build the image
docker build -t social-media-api .

# Run the container
docker run -p 5001:5001 social-media-api

# Run with volume for database persistence
docker run -p 5001:5001 -v $(pwd)/data:/app/data social-media-api
```

#### Pull from GitHub Container Registry

After pushing to GitHub, the container is automatically built and available at:
```bash
docker pull ghcr.io/vadimsteshkov/socialmediaapp:latest
docker run -p 5001:5001 ghcr.io/vadimsteshkov/socialmediaapp:latest
```

See [DOCKER.md](DOCKER.md) for detailed Docker documentation.

### Accessing the Web Interface

Once the server is running, open your browser and navigate to:
```
http://localhost:5001
```

The web interface provides:
- **Submit Post**: Create new posts
- **All Posts**: View all posts
- **Search**: Search posts by username

### API Endpoints

- `GET /api/posts` - Get all posts
- `POST /api/posts` - Create a new post
- `GET /api/posts/{id}` - Get a specific post by ID
- `GET /api/posts/search?user={username}` - Search posts by user
- `GET /api/posts/search?text={query}` - Search posts by text
- `GET /api/health` - Health check

### API Documentation

FastAPI automatically provides interactive API documentation:

- **Swagger UI**: `http://localhost:5001/docs`
- **OpenAPI JSON**: `http://localhost:5001/openapi.json`

### Getting OpenAPI JSON Specification

To save the OpenAPI JSON specification to a file:

**With formatting (recommended):**
```bash
curl -s http://localhost:5001/openapi.json | python -m json.tool > openapi.json
```

**Without formatting (minified):**
```bash
curl http://localhost:5001/openapi.json -o openapi.json
```

**Note:** The server must be running for these commands to work.

### Running the Original Application

```bash
python app.py
```

This will:
1. Create 3 sample posts in the database
2. Display the latest post

### Running Tests

**Database tests:**
```bash
pytest test_app.py -v
```

**REST API tests:**
```bash
pytest test_api.py -v
```

**All tests:**
```bash
pytest test_*.py -v
```

**With coverage report:**
```bash
pytest test_*.py -v --cov=. --cov-report=html
```

## Database Schema

The `posts` table contains the following fields:
- `id`: Primary key (auto-increment)
- `image`: Image URL or path (TEXT)
- `text`: Post text/comment (TEXT)
- `user`: Username (TEXT)
- `created_at`: Timestamp of post creation (TIMESTAMP)

## GitHub Actions

The project includes GitHub Actions workflows:

### Test Workflow (`.github/workflows/test.yml`)
- Runs automatically on pull requests to `main` branch
- Tests the application using the test suite

### Docker Build Workflow (`.github/workflows/docker-build.yml`)
- Automatically builds Docker container on push to `main` or `feature/docker-container`
- Pushes container to GitHub Container Registry (ghcr.io)
- Uses caching for faster builds
- Container available at: `ghcr.io/vadimsteshkov/socialmediaapp`

## Database Management via Terminal

You can manage posts directly through SQLite commands in the terminal:

### View Posts

```bash
# View all posts
sqlite3 social_media.db "SELECT id, user, text FROM posts;"

# Count posts
sqlite3 social_media.db "SELECT COUNT(*) FROM posts;"

# View latest post
sqlite3 social_media.db "SELECT * FROM posts ORDER BY created_at DESC LIMIT 1;"
```

### Delete Posts

```bash
# Delete a specific post by ID
sqlite3 social_media.db "DELETE FROM posts WHERE id = 1;"

# Delete all posts (keeps ID counter)
sqlite3 social_media.db "DELETE FROM posts;"

# Delete all posts AND reset ID counter to start from 1
sqlite3 social_media.db "DELETE FROM posts; DELETE FROM sqlite_sequence WHERE name='posts';"

# Delete posts by user
sqlite3 social_media.db "DELETE FROM posts WHERE user = 'alice_smith';"
```

## Sample Posts

The application includes 3 sample posts:
1. Sunset post by `alice_smith`
2. Coffee post by `bob_jones`
3. Mountain hiking post by `charlie_brown`
# Test GitHub Actions
