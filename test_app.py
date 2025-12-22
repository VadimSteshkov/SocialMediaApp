"""
Test suite for the social media app.
Tests database operations and post retrieval.
"""
import os
import pytest
from database import Database


@pytest.fixture
def test_db():
    """Create a test database."""
    test_db_path = "test_social_media.db"
    db = Database(db_path=test_db_path)
    db.delete_all_posts()
    yield db
    # Cleanup
    if os.path.exists(test_db_path):
        os.remove(test_db_path)


def test_insert_post(test_db):
    """Test inserting a post into the database."""
    post_id = test_db.insert_post(
        image="https://example.com/test.jpg",
        text="Test post",
        user="test_user"
    )
    
    assert post_id is not None
    assert isinstance(post_id, int)
    assert post_id > 0


def test_get_latest_post(test_db):
    """Test retrieving the latest post."""
    # Insert multiple posts
    test_db.insert_post(
        image="https://example.com/first.jpg",
        text="First post",
        user="user1"
    )
    
    test_db.insert_post(
        image="https://example.com/second.jpg",
        text="Second post",
        user="user2"
    )
    
    test_db.insert_post(
        image="https://example.com/third.jpg",
        text="Third post",
        user="user3"
    )
    
    # Get latest post
    latest = test_db.get_latest_post()
    
    assert latest is not None
    post_id, image, image_thumbnail, text, user, sentiment, sentiment_score, created_at = latest
    
    # Latest post should be the third one
    assert text == "Third post"
    assert user == "user3"
    assert image == "https://example.com/third.jpg"
    assert image_thumbnail is None  # No thumbnail for test posts


def test_get_latest_post_empty_database(test_db):
    """Test retrieving latest post from empty database."""
    latest = test_db.get_latest_post()
    assert latest is None


def test_get_all_posts(test_db):
    """Test retrieving all posts."""
    # Insert multiple posts
    test_db.insert_post(
        image="https://example.com/post1.jpg",
        text="Post 1",
        user="user1"
    )
    test_db.insert_post(
        image="https://example.com/post2.jpg",
        text="Post 2",
        user="user2"
    )
    
    all_posts = test_db.get_all_posts()
    
    assert len(all_posts) == 2
    # Tuple structure: (id, image, image_thumbnail, text, user, sentiment, sentiment_score, created_at)
    assert all_posts[0][3] == "Post 2"  # Latest first (text is at index 3)
    assert all_posts[1][3] == "Post 1"


def test_post_fields(test_db):
    """Test that all required fields are stored correctly."""
    test_db.insert_post(
        image="https://example.com/image.jpg",
        text="Test comment",
        user="testuser"
    )
    
    latest = test_db.get_latest_post()
    assert latest is not None
    
    post_id, image, image_thumbnail, text, user, sentiment, sentiment_score, created_at = latest
    
    assert image == "https://example.com/image.jpg"
    assert image_thumbnail is None  # No thumbnail for test posts
    assert text == "Test comment"
    assert user == "testuser"
    assert created_at is not None
    assert sentiment is None  # No sentiment for test posts
    assert sentiment_score is None  # No sentiment score for test posts


def test_update_post_sentiment(test_db):
    """Test updating sentiment analysis result for a post."""
    # Insert a post
    post_id = test_db.insert_post(
        image="https://example.com/image.jpg",
        text="I love this app!",
        user="testuser"
    )
    
    # Update sentiment
    test_db.update_post_sentiment(post_id, "POSITIVE", 0.95)
    
    # Retrieve post and check sentiment
    post = test_db.get_post_by_id(post_id)
    assert post is not None
    
    post_id_retrieved, image, image_thumbnail, text, user, sentiment, sentiment_score, created_at = post
    
    assert sentiment == "POSITIVE"
    assert sentiment_score == 0.95
    assert post_id_retrieved == post_id
