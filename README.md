# SocialMediaApp

Simple social media app for the Software Engineering course. This application stores social media posts in a SQLite database with support for images, text comments, and user information.

## Features

- Store social media posts with image, text, and user information
- Retrieve the latest post from the database
- Comprehensive test suite
- GitHub Actions CI/CD for automated testing on pull requests

## Project Structure

```
SocialMediaApp/
├── app.py              # Main application with sample posts
├── database.py         # Database operations and schema
├── test_app.py         # Test suite
├── requirements.txt    # Python dependencies
└── .github/
    └── workflows/
        └── test.yml    # GitHub Actions workflow
```

## Requirements

- Python 3.11 or higher
- No external dependencies (uses Python standard library)

## Usage

### Running the Application

```bash
python app.py
```

This will:
1. Create 3 sample posts in the database
2. Display the latest post

### Running Tests

**Using pytest (recommended - better output):**

```bash
# Install dependencies first
pip install -r requirements.txt

# Run tests with pytest (colorful, detailed output)
pytest test_app.py -v

# Or with coverage report
pytest test_app.py -v --cov=. --cov-report=html
```

**Using unittest (standard library):**

```bash
python -m unittest test_app -v
```

**Pytest provides:**
- Color-coded output (green for passed, red for failed)
- Progress indicators (20%, 40%, etc.)
- Detailed timing information
- Better error messages and stack traces
- Platform and Python version info

## Database Schema

The `posts` table contains the following fields:
- `id`: Primary key (auto-increment)
- `image`: Image URL or path (TEXT)
- `text`: Post text/comment (TEXT)
- `user`: Username (TEXT)
- `created_at`: Timestamp of post creation (TIMESTAMP)

## GitHub Actions

The project includes a GitHub Actions workflow (`.github/workflows/test.yml`) that:
- Runs automatically on pull requests to `main` or `master` branches
- Tests the application using the test suite
- Can be manually triggered via workflow_dispatch

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
