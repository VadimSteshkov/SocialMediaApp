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
from datetime import datetime, timedelta
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
    # Database will automatically detect PostgreSQL if DB_HOST is set,
    # otherwise falls back to SQLite
    return Database()

db = get_db()


# Pydantic models for request/response
class PostCreate(BaseModel):
    image: str
    text: str
    user: str
    tags: Optional[List[str]] = []


class PostResponse(BaseModel):
    id: int
    image: str
    text: str
    user: str
    created_at: str
    likes_count: int = 0
    is_liked: bool = False
    comments_count: int = 0
    tags: List[str] = []


class CommentCreate(BaseModel):
    user: str
    text: str


class CommentResponse(BaseModel):
    id: int
    user: str
    text: str
    created_at: str


class TimerResponse(BaseModel):
    can_post: bool
    time_remaining: Optional[int] = None  # seconds until next post allowed


class HealthResponse(BaseModel):
    status: str


def post_to_dict(post_tuple, current_user: Optional[str] = None):
    """Convert post tuple to dictionary with additional info."""
    if not post_tuple:
        return None
    post_id, image, text, user, created_at = post_tuple
    
    # Get additional info
    likes_count = db.get_like_count(post_id)
    is_liked = db.is_liked_by_user(post_id, current_user) if current_user else False
    comments = db.get_comments(post_id)
    tags = db.get_post_tags(post_id)
    
    return {
        'id': post_id,
        'image': image,
        'text': text,
        'user': user,
        'created_at': created_at.isoformat() if isinstance(created_at, datetime) else str(created_at),
        'likes_count': likes_count,
        'is_liked': is_liked,
        'comments_count': len(comments),
        'tags': tags
    }


@app.get("/api/posts/timer/{user}", response_model=TimerResponse)
async def get_post_timer(user: str):
    """Get timer information for a user (when they can post next)."""
    try:
        last_post_time = db.get_user_last_post_time(user)
        
        if not last_post_time:
            return {"can_post": True, "time_remaining": None}
        
        # Cooldown period: 1 hour (3600 seconds)
        COOLDOWN_SECONDS = 3600
        time_since_last_post = (datetime.now() - last_post_time).total_seconds()
        
        if time_since_last_post >= COOLDOWN_SECONDS:
            return {"can_post": True, "time_remaining": None}
        else:
            time_remaining = int(COOLDOWN_SECONDS - time_since_last_post)
            return {"can_post": False, "time_remaining": time_remaining}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/posts", response_model=PostResponse, status_code=201)
async def create_post(post: PostCreate):
    """Create a new post."""
    try:
        # Check if user can post (timer check)
        last_post_time = db.get_user_last_post_time(post.user)
        if last_post_time:
            COOLDOWN_SECONDS = 3600  # 1 hour
            time_since_last_post = (datetime.now() - last_post_time).total_seconds()
            if time_since_last_post < COOLDOWN_SECONDS:
                time_remaining = int(COOLDOWN_SECONDS - time_since_last_post)
                raise HTTPException(
                    status_code=429,
                    detail=f"Please wait {time_remaining} seconds before posting again"
                )
        
        post_id = db.insert_post(image=post.image, text=post.text, user=post.user)
        
        # Extract and add tags from text (automatic extraction as backup)
        import re
        hashtag_pattern = r'#([\w\u0400-\u04FF]+)'
        extracted_tags = [tag.lower() for tag in re.findall(hashtag_pattern, post.text)]
        
        # Combine with tags from request (if any) and remove duplicates
        all_tags = list(set((post.tags or []) + extracted_tags))
        
        # Add tags if any found
        if all_tags:
            db.add_tags_to_post(post_id, all_tags)
        
        created_post = db.get_post_by_id(post_id)
        if not created_post:
            raise HTTPException(status_code=500, detail="Failed to retrieve created post")
        return post_to_dict(created_post, current_user=post.user)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/posts", response_model=List[PostResponse])
async def get_all_posts(current_user: Optional[str] = Query(None, description="Current user for like status")):
    """Get all posts."""
    try:
        posts = db.get_all_posts()
        return [post_to_dict(post, current_user=current_user) for post in posts]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/posts/search", response_model=List[PostResponse])
async def search_posts(
    user: Optional[str] = Query(None, description="Search for posts by username"),
    text: Optional[str] = Query(None, description="Search for posts containing this text"),
    tag: Optional[str] = Query(None, description="Search for posts by tag"),
    current_user: Optional[str] = Query(None, description="Current user for like status")
):
    """Search for posts by user, text, or tag."""
    try:
        if not user and not text and not tag:
            raise HTTPException(
                status_code=400,
                detail="At least one search parameter is required (user, text, or tag)"
            )
        
        posts = []
        if tag:
            posts = db.search_posts_by_tag(tag)
        elif user:
            posts = db.search_posts_by_user(user)
        elif text:
            posts = db.search_posts_by_text(text)
        
        return [post_to_dict(post, current_user=current_user) for post in posts]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/posts/{post_id}", response_model=PostResponse)
async def get_post(post_id: int, current_user: Optional[str] = Query(None, description="Current user for like status")):
    """Get a specific post by ID."""
    try:
        post = db.get_post_by_id(post_id)
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        return post_to_dict(post, current_user=current_user)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/posts/{post_id}/like")
async def toggle_like(post_id: int, user: str = Query(..., description="User who is liking/unliking")):
    """Toggle like on a post."""
    try:
        # Check if post exists
        post = db.get_post_by_id(post_id)
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        
        # Toggle like
        if db.is_liked_by_user(post_id, user):
            db.remove_like(post_id, user)
            liked = False
        else:
            db.add_like(post_id, user)
            liked = True
        
        likes_count = db.get_like_count(post_id)
        return {"liked": liked, "likes_count": likes_count}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/posts/{post_id}/comments", response_model=CommentResponse, status_code=201)
async def add_comment(post_id: int, comment: CommentCreate):
    """Add a comment to a post."""
    try:
        # Check if post exists
        post = db.get_post_by_id(post_id)
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        
        comment_id = db.add_comment(post_id, comment.user, comment.text)
        comments = db.get_comments(post_id)
        
        # Find the created comment
        created_comment = None
        for c in comments:
            if c[0] == comment_id:
                created_comment = c
                break
        
        if not created_comment:
            raise HTTPException(status_code=500, detail="Failed to retrieve created comment")
        
        comment_id, user, text, created_at = created_comment
        return {
            "id": comment_id,
            "user": user,
            "text": text,
            "created_at": created_at.isoformat() if isinstance(created_at, datetime) else str(created_at)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/posts/{post_id}/comments", response_model=List[CommentResponse])
async def get_comments(post_id: int):
    """Get all comments for a post."""
    try:
        # Check if post exists
        post = db.get_post_by_id(post_id)
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        
        comments = db.get_comments(post_id)
        return [
            {
                "id": c[0],
                "user": c[1],
                "text": c[2],
                "created_at": c[3].isoformat() if isinstance(c[3], datetime) else str(c[3])
            }
            for c in comments
        ]
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


# Serve static files at root level for CSS, JS, and images (must be after all API routes)
@app.get("/style.css")
async def serve_css():
    """Serve CSS file."""
    return FileResponse("static/style.css")


@app.get("/app.js")
async def serve_js():
    """Serve JavaScript file."""
    return FileResponse("static/app.js")


@app.get("/logo.png")
async def serve_logo():
    """Serve logo file."""
    import os
    # Try multiple possible paths
    possible_paths = [
        "static/logo.png",
        os.path.join("static", "logo.png"),
        os.path.join(os.path.dirname(__file__), "static", "logo.png"),
    ]
    
    for logo_path in possible_paths:
        if os.path.exists(logo_path) and os.path.isfile(logo_path):
            return FileResponse(logo_path, media_type="image/png")
    
    # If not found, return error with debug info
    import sys
    raise HTTPException(
        status_code=404, 
        detail=f"Logo not found. Checked: {possible_paths}. CWD: {os.getcwd()}"
    )


if __name__ == '__main__':
    import uvicorn
    port = int(os.getenv('PORT', 5001))
    uvicorn.run(app, host='0.0.0.0', port=port)
