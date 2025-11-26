"""
FastAPI REST API for the social media app.
Provides endpoints for creating, retrieving, and searching posts.
"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from database import Database
from datetime import datetime
import os

# Initialize FastAPI app
app = FastAPI(
    title="Social Media App API",
    description="REST API for managing social media posts",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database
def get_db():
    """Get database instance. Allows override for testing."""
    return Database(db_path=os.getenv('DB_PATH', 'social_media.db'))

db = get_db()


# Pydantic models for request/response
class PostCreate(BaseModel):
    image: str
    text: str
    user: str


class PostResponse(BaseModel):
    id: int
    image: str
    text: str
    user: str
    created_at: str


class HealthResponse(BaseModel):
    status: str


def post_to_dict(post_tuple):
    """Convert post tuple to dictionary."""
    if not post_tuple:
        return None
    post_id, image, text, user, created_at = post_tuple
    return {
        'id': post_id,
        'image': image,
        'text': text,
        'user': user,
        'created_at': created_at.isoformat() if isinstance(created_at, datetime) else str(created_at)
    }


@app.post("/api/posts", response_model=PostResponse, status_code=201)
async def create_post(post: PostCreate):
    """Create a new post."""
    try:
        post_id = db.insert_post(image=post.image, text=post.text, user=post.user)
        created_post = db.get_post_by_id(post_id)
        if not created_post:
            raise HTTPException(status_code=500, detail="Failed to retrieve created post")
        return post_to_dict(created_post)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/posts", response_model=List[PostResponse])
async def get_all_posts():
    """Get all posts."""
    try:
        posts = db.get_all_posts()
        return [post_to_dict(post) for post in posts]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/posts/search", response_model=List[PostResponse])
async def search_posts(
    user: Optional[str] = Query(None, description="Search for posts by username"),
    text: Optional[str] = Query(None, description="Search for posts containing this text")
):
    """Search for posts by user or text."""
    try:
        if not user and not text:
            raise HTTPException(
                status_code=400,
                detail="At least one search parameter is required (user or text)"
            )
        
        posts = []
        if user:
            posts = db.search_posts_by_user(user)
        elif text:
            posts = db.search_posts_by_text(text)
        
        return [post_to_dict(post) for post in posts]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/posts/{post_id}", response_model=PostResponse)
async def get_post(post_id: int):
    """Get a specific post by ID."""
    try:
        post = db.get_post_by_id(post_id)
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        return post_to_dict(post)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/")
async def index():
    """Serve the main HTML page."""
    return FileResponse("static/index.html")


# Serve static files at root level for CSS and JS (must be after all API routes)
@app.get("/style.css")
async def serve_css():
    """Serve CSS file."""
    return FileResponse("static/style.css")


@app.get("/app.js")
async def serve_js():
    """Serve JavaScript file."""
    return FileResponse("static/app.js")


if __name__ == '__main__':
    import uvicorn
    port = int(os.getenv('PORT', 5001))
    uvicorn.run(app, host='0.0.0.0', port=port)
