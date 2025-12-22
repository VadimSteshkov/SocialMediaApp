# Social Media Application

A modern social media application built with microservices architecture, featuring machine learning capabilities for sentiment analysis, text generation, and translation. This project demonstrates a complete full-stack application with REST API, web frontend, and asynchronous processing using message queues.

## 📋 Table of Contents

- [Overview](#overview)
- [Project Evolution (Exercises 1-6)](#project-evolution-exercises-1-6)
- [Features](#features)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Microservices](#microservices)
- [Testing](#testing)
- [Deployment](#deployment)
- [Project Structure](#project-structure)

## 🎯 Overview

This social media application allows users to:
- Create posts with images and text
- Like and comment on posts
- Search posts by user, text, or tags
- View sentiment analysis of posts
- Generate text using AI
- Translate posts to different languages

The application is built using:
- **Backend**: FastAPI (Python)
- **Frontend**: HTML, CSS, JavaScript
- **Database**: PostgreSQL (production) / SQLite (development)
- **Message Queue**: RabbitMQ
- **Containerization**: Docker & Docker Compose
- **ML Models**: Hugging Face Transformers (GPT-2, RoBERTa, MarianMT)

## 📚 Project Evolution (Exercises 1-6)

### Exercise 1: Basic REST API
**Goal**: Create a simple REST API for social media posts

**What was added**:
- FastAPI REST API server (`api.py`)
- SQLite database with posts table (`database.py`)
- Basic CRUD operations for posts
- Web frontend (HTML/CSS/JavaScript)
- OpenAPI/Swagger documentation

**Key Files**:
- `api.py` - FastAPI application
- `database.py` - Database operations
- `static/` - Frontend files

### Exercise 2: Social Features
**Goal**: Add social interactions (likes, comments, tags)

**What was added**:
- Like/unlike functionality
- Comments system
- Hashtag support and tag extraction
- User search and post search
- Timer-based posting restrictions (1 hour cooldown)

**Key Features**:
- Users can like posts
- Users can comment on posts
- Automatic hashtag extraction from text
- Search by username, text, or tags

### Exercise 3: Docker Containerization
**Goal**: Containerize the application

**What was added**:
- `Dockerfile` for API service
- `docker-compose.yml` for local development
- Docker health checks
- GitHub Actions for automated Docker builds
- Container registry integration (GitHub Container Registry)

**Key Files**:
- `Dockerfile` - API container definition
- `docker-compose.yml` - Multi-container orchestration
- `.github/workflows/docker-build.yml` - CI/CD pipeline

### Exercise 4: Database Migration
**Goal**: Support both SQLite and PostgreSQL

**What was added**:
- PostgreSQL support in `database.py`
- Environment-based database selection
- Automatic schema migration
- Database connection pooling

**Configuration**:
- Set `DB_HOST` environment variable to use PostgreSQL
- Defaults to SQLite if `DB_HOST` is not set

### Exercise 5: Image Resize Microservice
**Goal**: Implement asynchronous image processing

**What was added**:
- Image Resize Microservice (`image_resize_service.py`)
- RabbitMQ message queue integration
- Thumbnail generation (300x300px)
- Full-size and thumbnail storage
- Asynchronous processing workflow

**Key Features**:
- Automatic thumbnail generation on image upload
- Full-size images stored separately
- Click-to-view full-size images with Instagram-like modal
- Comments visible in image modal

**Key Files**:
- `image_resize_service.py` - Image processing microservice
- `Dockerfile.resize` - Resize service container
- `requirements-resize.txt` - Image processing dependencies

### Exercise 6: ML Microservices
**Goal**: Add machine learning capabilities using pre-trained models

**What was added**:

#### 6.1 Sentiment Analysis Microservice
- Sentiment analysis using `cardiffnlp/twitter-roberta-base-sentiment`
- Automatic sentiment detection (POSITIVE/NEGATIVE/NEUTRAL)
- Sentiment icons displayed on posts (green/red/yellow)
- Sentiment scores stored in database

#### 6.2 Text Generation Microservice
- Text generation using GPT-2 model
- Generate posts based on user input or tags
- UI button for text generation
- Configurable generation parameters

#### 6.3 Translation Microservice (Additional)
- Multi-language translation using Helsinki-NLP models
- Support for: English, Russian, German, Spanish, French
- Automatic language detection
- Language-aware UI (translate link in post's language)
- Long text support with chunking

**Key Files**:
- `sentiment_analysis_service.py` - Sentiment analysis microservice
- `text_generation_service.py` - Text generation microservice
- `translation_service.py` - Translation microservice
- `Dockerfile.sentiment`, `Dockerfile.textgen`, `Dockerfile.translation`
- `requirements-sentiment.txt`, `requirements-textgen.txt`, `requirements-translation.txt`
- `test_translation.py` - Translation service tests

## ✨ Features

### Core Features
- ✅ Create posts with images and text
- ✅ Like and comment on posts
- ✅ Search posts by user, text, or tags
- ✅ User authentication (username-based)
- ✅ Post cooldown timer (1 hour between posts)

### Image Features
- ✅ Image upload (drag & drop or file picker)
- ✅ Automatic thumbnail generation
- ✅ Full-size image viewing with comments
- ✅ Image URL support

### Machine Learning Features
- ✅ **Sentiment Analysis**: Automatic sentiment detection with visual indicators
- ✅ **Text Generation**: AI-powered post text generation
- ✅ **Translation**: Multi-language post translation

### Social Features
- ✅ Hashtag support (#tag)
- ✅ Tag-based search
- ✅ Like counts and comment counts
- ✅ User-specific like tracking

## 🏗️ Architecture

### Microservices Architecture

```
┌─────────────┐
│   Web UI    │
│  (Browser)  │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  REST API   │
│  (FastAPI)  │
└──────┬──────┘
       │
       ├──► PostgreSQL Database
       │
       ├──► RabbitMQ Message Queue
       │    │
       │    ├──► Image Resize Service
       │    ├──► Sentiment Analysis Service
       │    ├──► Text Generation Service
       │    └──► Translation Service
       │
       └──► File Storage (uploads/)
```

### Services

1. **API Service** (`api.py`)
   - REST API endpoints
   - Request routing
   - Message queue integration

2. **Image Resize Service** (`image_resize_service.py`)
   - Asynchronous image processing
   - Thumbnail generation

3. **Sentiment Analysis Service** (`sentiment_analysis_service.py`)
   - Post sentiment analysis
   - Database updates

4. **Text Generation Service** (`text_generation_service.py`)
   - GPT-2 text generation
   - Response queue handling

5. **Translation Service** (`translation_service.py`)
   - Multi-language translation
   - Language detection

### Technology Stack

- **Backend Framework**: FastAPI 0.104+
- **Database**: PostgreSQL 15 / SQLite 3
- **Message Queue**: RabbitMQ 3
- **ML Framework**: Hugging Face Transformers
- **Image Processing**: Pillow (PIL)
- **Containerization**: Docker & Docker Compose
- **CI/CD**: GitHub Actions

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Git (for cloning the repository)

### One-Command Setup

```bash
# Clone the repository
git clone https://github.com/VadimSteshkov/SocialMediaApp.git
cd SocialMediaApp

# Start all services
docker-compose up -d

# Wait for services to start (about 30-60 seconds)
docker-compose ps

# Access the application
open http://localhost:5001
```

That's it! The application is now running with all microservices.

## 📦 Installation

### Option 1: Docker Compose (Recommended)

**For New Users - Easiest Way:**

1. **Clone the repository:**
   ```bash
   git clone https://github.com/VadimSteshkov/SocialMediaApp.git
   cd SocialMediaApp
   ```

2. **Start all services:**
   ```bash
   docker-compose up -d
   ```

3. **Check service status:**
   ```bash
   docker-compose ps
   ```

4. **View logs (if needed):**
   ```bash
   docker-compose logs -f api
   ```

5. **Access the application:**
   - Web UI: http://localhost:5001
   - API Docs: http://localhost:5001/docs
   - RabbitMQ Management: http://localhost:15673 (guest/guest)

6. **Stop services:**
   ```bash
   docker-compose down
   ```

### Option 2: Local Development (Without Docker)

**Requirements:**
- Python 3.12+
- PostgreSQL 15 (optional, SQLite used by default)
- RabbitMQ server

**Steps:**

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up PostgreSQL (optional):**
   ```bash
   export DB_TYPE=postgresql
   export DB_HOST=localhost
   export DB_NAME=social_media
   export DB_USER=postgres
   export DB_PASSWORD=postgres
   ```

3. **Start RabbitMQ:**
   ```bash
   # Using Docker
   docker run -d --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3-management
   
   # Or install locally and run:
   # rabbitmq-server
   ```

4. **Start the API:**
   ```bash
   python api.py
   ```

5. **Start microservices (in separate terminals):**
   ```bash
   # Terminal 2: Image Resize Service
   python image_resize_service.py
   
   # Terminal 3: Sentiment Analysis Service
   python sentiment_analysis_service.py
   
   # Terminal 4: Text Generation Service
   python text_generation_service.py
   
   # Terminal 5: Translation Service
   python translation_service.py
   ```

## 💻 Usage

### Web Interface

Access the application at `http://localhost:5001`

**Features:**
- **Submit Post**: Create new posts with images and text
- **All Posts**: View all posts with likes, comments, and sentiment
- **Search**: Search posts by username (@user), text, or tags (#tag)

### Creating a Post

1. Enter your username
2. Write post text (use #hashtags for tags)
3. Upload an image (drag & drop or click to browse)
4. Click "Submit Post"
5. Wait for image processing and sentiment analysis (automatic)

### Using ML Features

#### Sentiment Analysis
- Automatically runs when you create a post
- Sentiment icon appears in the bottom right of each post:
  - 🟢 Green = Positive
  - 🔴 Red = Negative
  - 🟡 Yellow = Neutral

#### Text Generation
1. Start writing a post or enter tags
2. Click "Generate Text" button
3. AI will generate text based on your input
4. Edit the generated text if needed
5. Submit the post

#### Translation
1. View any post
2. Click "Translate text" link (appears in post's language)
3. Text is translated (English ↔ German by default)
4. Click again to show original

### API Endpoints

#### Posts
- `GET /api/posts` - Get all posts
- `POST /api/posts` - Create a new post
- `GET /api/posts/{id}` - Get a specific post
- `POST /api/posts/{id}/like` - Like/unlike a post
- `POST /api/posts/{id}/comments` - Add a comment
- `GET /api/posts/{id}/comments` - Get comments

#### Search
- `GET /api/posts/search?user={username}` - Search by user
- `GET /api/posts/search?text={query}` - Search by text
- `GET /api/posts/search?tag={tag}` - Search by tag

#### ML Features
- `POST /api/posts/generate-text` - Generate text using AI
- `POST /api/posts/{id}/translate` - Translate post text

#### Utility
- `GET /api/health` - Health check
- `GET /api/posts/timer/{user}` - Check posting cooldown

### API Documentation

FastAPI provides interactive API documentation:

- **Swagger UI**: http://localhost:5001/docs
- **ReDoc**: http://localhost:5001/redoc
- **OpenAPI JSON**: http://localhost:5001/openapi.json

## 🔧 Microservices

### Image Resize Service

**Purpose**: Generate thumbnails for uploaded images

**Queue**: `image_resize_queue`

**Process**:
1. API sends image path to queue
2. Service processes image (resize to 300x300px)
3. Saves thumbnail to `uploads/thumbnails/`
4. Updates database with thumbnail path

**Dependencies**: Pillow

### Sentiment Analysis Service

**Purpose**: Analyze post sentiment

**Queue**: `sentiment_analysis_queue`

**Model**: `cardiffnlp/twitter-roberta-base-sentiment`

**Process**:
1. API sends post text to queue
2. Service analyzes sentiment
3. Updates database with sentiment and score

**Dependencies**: transformers, torch, sentencepiece

### Text Generation Service

**Purpose**: Generate text using GPT-2

**Queues**: `text_generation_queue`, `text_generation_response_queue`

**Model**: `gpt2`

**Process**:
1. API sends request with prompt/tags
2. Service generates text
3. Returns generated text via response queue

**Dependencies**: transformers, torch

### Translation Service

**Purpose**: Translate posts between languages

**Queues**: `translation_queue`, `translation_response_queue`

**Models**: Helsinki-NLP MarianMT models

**Supported Languages**: EN, RU, DE, ES, FR

**Process**:
1. API sends text and target language
2. Service detects source language
3. Translates text (handles long texts with chunking)
4. Returns translated text

**Dependencies**: transformers, torch, sentencepiece

## 🧪 Testing

### Run All Tests

```bash
pytest test_*.py -v
```

### Run Specific Test Suites

```bash
# Database tests
pytest test_app.py -v

# API tests
pytest test_api.py -v

# Social features tests
pytest test_social_features.py -v

# Translation service tests
pytest test_translation.py -v
```

### Test with Coverage

```bash
pytest test_*.py -v --cov=. --cov-report=html
```

### Test Individual Microservices

```bash
# Test translation service (requires dependencies)
pytest test_translation.py -v

# Note: ML service tests may skip if dependencies not available
```

## 🚢 Deployment

### Docker Compose Production

```bash
# Use production compose file
docker-compose -f docker-compose.prod.yml up -d
```

### Environment Variables

Create `.env` file:

```env
# Database
DB_TYPE=postgresql
DB_HOST=db
DB_PORT=5432
DB_NAME=social_media
DB_USER=postgres
DB_PASSWORD=your_password

# RabbitMQ
RABBITMQ_USER=guest
RABBITMQ_PASSWORD=your_password

# API
PORT=5001
```

### GitHub Container Registry

Images are automatically built and pushed to:
- `ghcr.io/vadimsteshkov/socialmediaapp:latest`
- `ghcr.io/vadimsteshkov/socialmediaapp-resize:latest`
- `ghcr.io/vadimsteshkov/socialmediaapp-sentiment:latest`
- `ghcr.io/vadimsteshkov/socialmediaapp-textgen:latest`
- `ghcr.io/vadimsteshkov/socialmediaapp-translation:latest`

Pull and run:
```bash
docker pull ghcr.io/vadimsteshkov/socialmediaapp:latest
docker run -p 5001:5001 ghcr.io/vadimsteshkov/socialmediaapp:latest
```

## 📁 Project Structure

```
SocialMediaApp/
├── api.py                      # FastAPI REST API server
├── database.py                 # Database operations (PostgreSQL/SQLite)
├── app.py                      # Sample data generator
│
├── Microservices/
│   ├── image_resize_service.py
│   ├── sentiment_analysis_service.py
│   ├── text_generation_service.py
│   └── translation_service.py
│
├── Dockerfiles/
│   ├── Dockerfile              # API service
│   ├── Dockerfile.resize       # Image resize service
│   ├── Dockerfile.sentiment    # Sentiment analysis service
│   ├── Dockerfile.textgen      # Text generation service
│   └── Dockerfile.translation  # Translation service
│
├── Requirements/
│   ├── requirements.txt        # API dependencies
│   ├── requirements-resize.txt
│   ├── requirements-sentiment.txt
│   ├── requirements-textgen.txt
│   └── requirements-translation.txt
│
├── Tests/
│   ├── test_app.py            # Database tests
│   ├── test_api.py            # API tests
│   ├── test_social_features.py # Social features tests
│   └── test_translation.py    # Translation service tests
│
├── static/                     # Web frontend
│   ├── index.html
│   ├── style.css
│   ├── app.js
│   └── icons/
│       └── logo.png
│
├── data/                       # Database files (SQLite)
│   └── social_media.db
│
├── uploads/                    # Uploaded images
│   ├── full/                   # Full-size images
│   └── thumbnails/             # Thumbnail images
│
├── docker-compose.yml          # Docker Compose configuration
├── .github/workflows/          # GitHub Actions
│   ├── test.yml               # Test workflow
│   └── docker-build.yml       # Build workflow
│
└── README.md                   # This file
```

## 🔐 Database Schema

### Posts Table
- `id` (SERIAL/INTEGER) - Primary key
- `image` (TEXT) - Image URL/path
- `image_thumbnail` (TEXT) - Thumbnail URL/path
- `text` (TEXT) - Post content
- `user` (TEXT) - Username
- `sentiment` (TEXT) - Sentiment label (POSITIVE/NEGATIVE/NEUTRAL)
- `sentiment_score` (REAL) - Sentiment confidence (0.0-1.0)
- `created_at` (TIMESTAMP) - Creation timestamp

### Related Tables
- `likes` - Post likes (post_id, user)
- `comments` - Post comments (id, post_id, user, text, created_at)
- `tags` - Post tags (id, name)
- `post_tags` - Post-tag relationships (post_id, tag_id)
- `user_last_post` - User posting timestamps (user, last_post_time)

## 🔄 GitHub Actions

### Test Workflow (`.github/workflows/test.yml`)
- Runs on pull requests to `main`
- Tests application and microservices
- Python 3.11+ required

### Docker Build Workflow (`.github/workflows/docker-build.yml`)
- Builds and pushes Docker images on push
- Supports multiple branches:
  - `main`
  - `feature/docker-container`
  - `feature/image-resize-microservice`
  - `feature/ml-microservices`
- Builds all microservice images
- Pushes to GitHub Container Registry

## 🐛 Troubleshooting

### Services Not Starting

```bash
# Check logs
docker-compose logs api
docker-compose logs sentiment-analysis
docker-compose logs text-generation
docker-compose logs translation

# Restart specific service
docker-compose restart api
```

### Database Connection Issues

```bash
# Check database is running
docker-compose ps db

# Check database logs
docker-compose logs db

# Verify connection
docker-compose exec api python -c "from database import Database; db = Database(); print('Connected!')"
```

### RabbitMQ Connection Issues

```bash
# Check RabbitMQ is running
docker-compose ps rabbitmq

# Access RabbitMQ Management UI
open http://localhost:15673
# Login: guest / guest

# Check queues
docker-compose exec rabbitmq rabbitmqctl list_queues
```

### ML Services Not Working

```bash
# Check if models are downloading (first run takes time)
docker-compose logs sentiment-analysis | grep "Loading"
docker-compose logs text-generation | grep "Loading"
docker-compose logs translation | grep "Loading"

# Models download on first run (may take 5-10 minutes)
```

## 📝 License

This project is part of a Software Engineering course assignment.

## 👥 Author

Vadim Steshkov

## 🙏 Acknowledgments

- FastAPI for the excellent web framework
- Hugging Face for pre-trained ML models
- RabbitMQ for message queue functionality
- Docker for containerization

---

**For detailed Docker documentation, see [DOCKER.md](DOCKER.md)**
