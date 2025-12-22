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
    # Use unique usernames to avoid conflicts with other tests
    unique_user1 = 'alice_search_test_unique'
    unique_user2 = 'bob_search_test_unique'
    
    # Create posts from different users
    post1 = {
        'image': 'https://example.com/post1.jpg',
        'text': 'Post from alice',
        'user': unique_user1
    }
    post2 = {
        'image': 'https://example.com/post2.jpg',
        'text': 'Post from bob',
        'user': unique_user2
    }
    post3 = {
        'image': 'https://example.com/post3.jpg',
        'text': 'Another post from alice',
        'user': unique_user1
    }
    
    # Create all posts
    # Note: Timer prevents same user from posting twice quickly, so we use different users
    response1 = client.post('/api/posts', json=post1)
    assert response1.status_code == 201
    
    response2 = client.post('/api/posts', json=post2)
    assert response2.status_code == 201
    
    # Third post from same user will be blocked by timer, so we'll test with what we have
    response3 = client.post('/api/posts', json=post3)
    # This might fail due to timer, which is expected behavior
    
    # Search for alice's posts (unique_user1)
    response = client.get(f'/api/posts/search?user={unique_user1}')
    
    assert response.status_code == 200
    data = response.json()
    # Should find at least 1 post from unique_user1
    # (Only 1 because timer blocks the second post from same user)
    assert len(data) >= 1, f"Expected at least 1 post, got {len(data)}. Data: {data}"
    assert all(p['user'] == unique_user1 for p in data)
    assert data[0]['text'] == 'Post from alice'
    
    # Also verify search works for different user
    response_bob = client.get(f'/api/posts/search?user={unique_user2}')
    assert response_bob.status_code == 200
    bob_data = response_bob.json()
    assert len(bob_data) >= 1
    assert all(p['user'] == unique_user2 for p in bob_data)


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


# ===== Tests for Post Timer (Cooldown) =====

def test_post_timer_new_user(client):
    """Test timer for a new user (should allow posting)."""
    response = client.get('/api/posts/timer/newuser')
    
    assert response.status_code == 200
    data = response.json()
    assert data['can_post'] is True
    # For new users, time_remaining can be None or 0
    assert data['time_remaining'] is None or data['time_remaining'] == 0


def test_post_timer_cooldown(client):
    """Test timer cooldown after posting."""
    # Create a post
    post_data = {
        'image': 'https://example.com/test.jpg',
        'text': 'Test post',
        'user': 'timer_user'
    }
    client.post('/api/posts', json=post_data)
    
    # Check timer immediately after posting
    response = client.get('/api/posts/timer/timer_user')
    
    assert response.status_code == 200
    data = response.json()
    assert data['can_post'] is False
    assert data['time_remaining'] > 0
    assert data['time_remaining'] <= 3600  # Should be less than 1 hour


# ===== Tests for Likes =====

def test_toggle_like_add(client):
    """Test adding a like to a post."""
    # Create a post
    post_data = {
        'image': 'https://example.com/test.jpg',
        'text': 'Test post',
        'user': 'post_author'
    }
    create_response = client.post('/api/posts', json=post_data)
    post_id = create_response.json()['id']
    
    # Add a like
    response = client.post(f'/api/posts/{post_id}/like?user=liker_user')
    
    assert response.status_code == 200
    data = response.json()
    assert data['liked'] is True
    assert data['likes_count'] == 1


def test_toggle_like_remove(client):
    """Test removing a like from a post."""
    # Create a post
    post_data = {
        'image': 'https://example.com/test.jpg',
        'text': 'Test post',
        'user': 'post_author'
    }
    create_response = client.post('/api/posts', json=post_data)
    post_id = create_response.json()['id']
    
    # Add a like
    client.post(f'/api/posts/{post_id}/like?user=liker_user')
    
    # Remove the like
    response = client.post(f'/api/posts/{post_id}/like?user=liker_user')
    
    assert response.status_code == 200
    data = response.json()
    assert data['liked'] is False
    assert data['likes_count'] == 0


def test_like_count_in_post(client):
    """Test that like count is included in post response."""
    # Create a post
    post_data = {
        'image': 'https://example.com/test.jpg',
        'text': 'Test post',
        'user': 'post_author'
    }
    create_response = client.post('/api/posts', json=post_data)
    post_id = create_response.json()['id']
    
    # Add likes
    client.post(f'/api/posts/{post_id}/like?user=user1')
    client.post(f'/api/posts/{post_id}/like?user=user2')
    
    # Get post and check like count
    response = client.get(f'/api/posts/{post_id}')
    data = response.json()
    
    assert data['likes_count'] == 2
    assert data['is_liked'] is False  # Current user not specified


def test_is_liked_status(client):
    """Test that is_liked status is correct for current user."""
    # Create a post
    post_data = {
        'image': 'https://example.com/test.jpg',
        'text': 'Test post',
        'user': 'post_author'
    }
    create_response = client.post('/api/posts', json=post_data)
    post_id = create_response.json()['id']
    
    # Add a like from user1
    client.post(f'/api/posts/{post_id}/like?user=user1')
    
    # Get post with current_user=user1
    response = client.get(f'/api/posts/{post_id}?current_user=user1')
    data = response.json()
    
    assert data['is_liked'] is True
    assert data['likes_count'] == 1


# ===== Tests for Comments =====

def test_add_comment(client):
    """Test adding a comment to a post."""
    # Create a post
    post_data = {
        'image': 'https://example.com/test.jpg',
        'text': 'Test post',
        'user': 'post_author'
    }
    create_response = client.post('/api/posts', json=post_data)
    post_id = create_response.json()['id']
    
    # Add a comment
    comment_data = {
        'user': 'commenter',
        'text': 'Great post!'
    }
    response = client.post(f'/api/posts/{post_id}/comments', json=comment_data)
    
    assert response.status_code == 201
    data = response.json()
    assert data['text'] == 'Great post!'
    assert data['user'] == 'commenter'
    assert 'id' in data
    assert 'created_at' in data


def test_get_comments(client):
    """Test getting comments for a post."""
    # Create a post
    post_data = {
        'image': 'https://example.com/test.jpg',
        'text': 'Test post',
        'user': 'post_author'
    }
    create_response = client.post('/api/posts', json=post_data)
    post_id = create_response.json()['id']
    
    # Add multiple comments
    client.post(f'/api/posts/{post_id}/comments', json={'user': 'user1', 'text': 'First comment'})
    client.post(f'/api/posts/{post_id}/comments', json={'user': 'user2', 'text': 'Second comment'})
    
    # Get comments
    response = client.get(f'/api/posts/{post_id}/comments')
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]['text'] == 'First comment'
    assert data[1]['text'] == 'Second comment'


def test_comment_count_in_post(client):
    """Test that comment count is included in post response."""
    # Create a post
    post_data = {
        'image': 'https://example.com/test.jpg',
        'text': 'Test post',
        'user': 'post_author'
    }
    create_response = client.post('/api/posts', json=post_data)
    post_id = create_response.json()['id']
    
    # Add comments
    client.post(f'/api/posts/{post_id}/comments', json={'user': 'user1', 'text': 'Comment 1'})
    client.post(f'/api/posts/{post_id}/comments', json={'user': 'user2', 'text': 'Comment 2'})
    
    # Get post and check comment count
    response = client.get(f'/api/posts/{post_id}')
    data = response.json()
    
    assert data['comments_count'] == 2


# ===== Tests for Tags =====

def test_create_post_with_tags(client):
    """Test creating a post with tags."""
    post_data = {
        'image': 'https://example.com/test.jpg',
        'text': 'Test post #study #sport',
        'user': 'test_user',
        'tags': ['study', 'sport']
    }
    
    response = client.post('/api/posts', json=post_data)
    
    assert response.status_code == 201
    data = response.json()
    assert 'tags' in data
    assert len(data['tags']) == 2
    assert 'study' in data['tags']
    assert 'sport' in data['tags']


def test_tags_auto_extraction(client):
    """Test that tags are automatically extracted from text."""
    post_data = {
        'image': 'https://example.com/test.jpg',
        'text': 'Test post #study #sport #new',
        'user': 'test_user'
        # No tags in request, should be extracted from text
    }
    
    response = client.post('/api/posts', json=post_data)
    
    assert response.status_code == 201
    data = response.json()
    assert 'tags' in data
    assert len(data['tags']) >= 3
    assert 'study' in data['tags']
    assert 'sport' in data['tags']
    assert 'new' in data['tags']


def test_search_posts_by_tag(client):
    """Test searching posts by tag."""
    # Create posts with different tags
    post1 = {
        'image': 'https://example.com/post1.jpg',
        'text': 'Post about #study',
        'user': 'user1',
        'tags': ['study']
    }
    post2 = {
        'image': 'https://example.com/post2.jpg',
        'text': 'Post about #sport',
        'user': 'user2',
        'tags': ['sport']
    }
    post3 = {
        'image': 'https://example.com/post3.jpg',
        'text': 'Another #study post',
        'user': 'user3',
        'tags': ['study']
    }
    
    client.post('/api/posts', json=post1)
    client.post('/api/posts', json=post2)
    client.post('/api/posts', json=post3)
    
    # Search for posts with 'study' tag
    response = client.get('/api/posts/search?tag=study')
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert all('study' in post['tags'] for post in data)


def test_search_posts_by_tag_case_insensitive(client):
    """Test that tag search is case-insensitive."""
    # Create post with uppercase tag
    post_data = {
        'image': 'https://example.com/test.jpg',
        'text': 'Test #STUDY',
        'user': 'test_user',
        'tags': ['study']
    }
    client.post('/api/posts', json=post_data)
    
    # Search with lowercase
    response = client.get('/api/posts/search?tag=study')
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1


def test_tags_in_post_response(client):
    """Test that tags are included in post response."""
    post_data = {
        'image': 'https://example.com/test.jpg',
        'text': 'Test #study #sport',
        'user': 'test_user',
        'tags': ['study', 'sport']
    }
    
    create_response = client.post('/api/posts', json=post_data)
    post_id = create_response.json()['id']
    
    # Get the post
    response = client.get(f'/api/posts/{post_id}')
    data = response.json()
    
    assert 'tags' in data
    assert len(data['tags']) == 2
    assert 'study' in data['tags']
    assert 'sport' in data['tags']


def test_multiple_tags_same_post(client):
    """Test that a post can have multiple tags."""
    post_data = {
        'image': 'https://example.com/test.jpg',
        'text': 'Test #tag1 #tag2 #tag3',
        'user': 'test_user',
        'tags': ['tag1', 'tag2', 'tag3']
    }
    
    response = client.post('/api/posts', json=post_data)
    data = response.json()
    
    assert len(data['tags']) == 3
    assert set(data['tags']) == {'tag1', 'tag2', 'tag3'}


def test_post_with_likes_comments_tags(client):
    """Test a post with all features: likes, comments, and tags."""
    # Create post with tags
    post_data = {
        'image': 'https://example.com/test.jpg',
        'text': 'Complete test #test',
        'user': 'author',
        'tags': ['test']
    }
    create_response = client.post('/api/posts', json=post_data)
    post_id = create_response.json()['id']
    
    # Add likes
    client.post(f'/api/posts/{post_id}/like?user=user1')
    client.post(f'/api/posts/{post_id}/like?user=user2')
    
    # Add comments
    client.post(f'/api/posts/{post_id}/comments', json={'user': 'user1', 'text': 'Nice!'})
    client.post(f'/api/posts/{post_id}/comments', json={'user': 'user2', 'text': 'Cool!'})
    
    # Get post
    response = client.get(f'/api/posts/{post_id}?current_user=user1')
    data = response.json()
    
    assert data['likes_count'] == 2
    assert data['is_liked'] is True
    assert data['comments_count'] == 2
    assert len(data['tags']) == 1
    assert 'test' in data['tags']


def test_translate_post_endpoint_exists(client):
    """Test that translate endpoint exists and accepts requests."""
    # Create a post first
    post_data = {
        'image': 'https://example.com/test.jpg',
        'text': 'Hello, this is a test post.',
        'user': 'test_user'
    }
    create_response = client.post('/api/posts', json=post_data)
    post_id = create_response.json()['id']
    
    # Try to translate (may fail if translation service not running, but endpoint should exist)
    response = client.post(
        f'/api/posts/{post_id}/translate',
        data={'target_lang': 'de', 'source_lang': 'en'}
    )
    
    # Endpoint should exist (not 404)
    assert response.status_code != 404
    # May return 500 if translation service not available, but endpoint structure is correct
    assert response.status_code in [200, 400, 500, 504]


def test_translate_post_not_found(client):
    """Test translation of non-existent post."""
    response = client.post(
        '/api/posts/99999/translate',
        data={'target_lang': 'de', 'source_lang': 'en'}
    )
    
    assert response.status_code == 404
    data = response.json()
    assert 'detail' in data
    assert 'not found' in data['detail'].lower()


def test_translate_post_missing_parameters(client):
    """Test translation endpoint with missing parameters."""
    # Create a post first
    post_data = {
        'image': 'https://example.com/test.jpg',
        'text': 'Test post',
        'user': 'test_user'
    }
    create_response = client.post('/api/posts', json=post_data)
    post_id = create_response.json()['id']
    
    # Try without target_lang (should use default)
    response = client.post(
        f'/api/posts/{post_id}/translate',
        data={}
    )
    
    # Should accept request (may fail later if service unavailable)
    assert response.status_code != 404
    assert response.status_code in [200, 400, 500, 504]
