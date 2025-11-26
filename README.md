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
├── requirements.txt    # Python dependencies
├── openapi.json        # OpenAPI specification (auto-generated)
├── static/             # Web frontend files
│   ├── index.html      # Main HTML page
│   ├── style.css       # Styles
│   └── app.js          # JavaScript client
└── .github/
    └── workflows/
        └── test.yml    # GitHub Actions workflow
```

## Requirements

- Python 3.11 or higher
- FastAPI and Uvicorn (see requirements.txt)

## Usage

### Installation

```bash
pip install -r requirements.txt
```

### Running the REST API Server

```bash
python api.py
```

The server will start on `http://localhost:5001` (or port specified by `PORT` environment variable).

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

The project includes a GitHub Actions workflow (`.github/workflows/test.yml`) that:
- Runs automatically on pull requests to `main` branch
- Tests the application using the test suite

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
