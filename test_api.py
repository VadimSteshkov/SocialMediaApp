"""
Test suite for the REST API.
Tests all API endpoints and functionality.
"""
import os
import pytest
import api
from fastapi.testclient import TestClient
from database import Database


@pytest.fixture
def test_db():
    """Create a test database and replace the api's db instance."""
    test_db_path = "test_social_media_api.db"
    test_db = Database(db_path=test_db_path)
    test_db.delete_all_posts()
    api.db = test_db  # Replace the module-level db instance
    yield test_db
    # Cleanup
    if hasattr(api, 'db') and api.db:
        api.db.delete_all_posts()
    if os.path.exists(test_db_path):
        os.remove(test_db_path)


@pytest.fixture
def client(test_db):
    """Create a test client for the API."""
    return TestClient(api.app)


def test_create_post_success(client):
    """Test creating a post successfully."""
    post_data = {
        'image': 'https://example.com/test.jpg',
        'text': 'Test post',
        'user': 'test_user'
    }
    
    response = client.post('/api/posts', json=post_data)
    
    assert response.status_code == 201
    data = response.json()
    assert data['text'] == 'Test post'
    assert data['user'] == 'test_user'
    assert 'id' in data
    assert 'created_at' in data


def test_create_post_missing_fields(client):
    """Test creating a post with missing required fields."""
    post_data = {
        'image': 'https://example.com/test.jpg',
        'text': 'Test post'
        # Missing 'user' field
    }
    
    response = client.post('/api/posts', json=post_data)
    
    assert response.status_code == 422  # FastAPI returns 422 for validation errors
    data = response.json()
    assert 'detail' in data


def test_create_post_empty_body(client):
    """Test creating a post with empty request body."""
    response = client.post('/api/posts', json={})
    
    assert response.status_code == 422


def test_get_all_posts_empty(client):
    """Test getting all posts when database is empty."""
    response = client.get('/api/posts')
    
    assert response.status_code == 200
    data = response.json()
    assert data == []


def test_get_all_posts(client):
    """Test getting all posts."""
    # Create some posts
    post1 = {
        'image': 'https://example.com/post1.jpg',
        'text': 'First post',
        'user': 'user1'
    }
    post2 = {
        'image': 'https://example.com/post2.jpg',
        'text': 'Second post',
        'user': 'user2'
    }
    
    client.post('/api/posts', json=post1)
    client.post('/api/posts', json=post2)
    
    response = client.get('/api/posts')
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    # Posts should be ordered by created_at DESC (newest first)
    assert data[0]['text'] == 'Second post'
    assert data[1]['text'] == 'First post'


def test_get_post_by_id_success(client):
    """Test getting a post by ID."""
    # Create a post
    post_data = {
        'image': 'https://example.com/test.jpg',
        'text': 'Test post',
        'user': 'test_user'
    }
    
    create_response = client.post('/api/posts', json=post_data)
    created_post = create_response.json()
    post_id = created_post['id']
    
    # Get the post by ID
    response = client.get(f'/api/posts/{post_id}')
    
    assert response.status_code == 200
    data = response.json()
    assert data['id'] == post_id
    assert data['text'] == 'Test post'


def test_get_post_by_id_not_found(client):
    """Test getting a post by non-existent ID."""
    response = client.get('/api/posts/999')
    
    assert response.status_code == 404
    data = response.json()
    assert 'detail' in data


def test_search_posts_by_user(client):
    """Test searching posts by username."""
    # Create posts from different users
    post1 = {
        'image': 'https://example.com/post1.jpg',
        'text': 'Post from alice',
        'user': 'alice'
    }
    post2 = {
        'image': 'https://example.com/post2.jpg',
        'text': 'Post from bob',
        'user': 'bob'
    }
    post3 = {
        'image': 'https://example.com/post3.jpg',
        'text': 'Another post from alice',
        'user': 'alice'
    }
    
    client.post('/api/posts', json=post1)
    client.post('/api/posts', json=post2)
    client.post('/api/posts', json=post3)
    
    # Search for alice's posts
    response = client.get('/api/posts/search?user=alice')
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]['user'] == 'alice'
    assert data[1]['user'] == 'alice'


def test_search_posts_by_text(client):
    """Test searching posts by text content."""
    # Create posts with different text
    post1 = {
        'image': 'https://example.com/post1.jpg',
        'text': 'Beautiful sunset today',
        'user': 'user1'
    }
    post2 = {
        'image': 'https://example.com/post2.jpg',
        'text': 'Morning coffee',
        'user': 'user2'
    }
    post3 = {
        'image': 'https://example.com/post3.jpg',
        'text': 'Another beautiful day',
        'user': 'user3'
    }
    
    client.post('/api/posts', json=post1)
    client.post('/api/posts', json=post2)
    client.post('/api/posts', json=post3)
    
    # Search for posts containing "beautiful"
    response = client.get('/api/posts/search?text=beautiful')
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert 'beautiful' in data[0]['text'].lower()
    assert 'beautiful' in data[1]['text'].lower()


def test_search_posts_no_parameters(client):
    """Test searching posts without parameters."""
    response = client.get('/api/posts/search')
    
    assert response.status_code == 400
    data = response.json()
    assert 'detail' in data


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get('/api/health')
    
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'healthy'
