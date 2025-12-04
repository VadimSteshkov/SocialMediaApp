"""
Test suite for social features: timer, likes, comments, tags.
Tests all social interaction API endpoints and functionality.
"""
import os
import pytest
import api
from fastapi.testclient import TestClient
from database import Database


@pytest.fixture
def test_db():
    """Create a test database and replace the api's db instance."""
    test_db_path = "test_new_features.db"
    test_db = Database(db_path=test_db_path)
    test_db.delete_all_posts()
    api.db = test_db  # Replace the module-level db instance
    yield test_db
    # Cleanup
    if hasattr(api, 'db') and api.db:
        test_db.delete_all_posts()
    if os.path.exists(test_db_path):
        os.remove(test_db_path)


@pytest.fixture
def client(test_db):
    """Create a test client for the API."""
    return TestClient(api.app)


# ===== Tests for Post Timer (Cooldown) =====

def test_post_timer_new_user(client):
    """Test timer for a new user (should allow posting)."""
    response = client.get('/api/posts/timer/newuser123')
    
    assert response.status_code == 200
    data = response.json()
    assert data['can_post'] is True
    assert data['time_remaining'] is None or data['time_remaining'] == 0


def test_post_timer_cooldown(client):
    """Test timer cooldown after posting."""
    # Create a post
    post_data = {
        'image': 'https://example.com/test.jpg',
        'text': 'Test post',
        'user': 'timer_user_cooldown'
    }
    client.post('/api/posts', json=post_data)
    
    # Check timer immediately after posting
    response = client.get('/api/posts/timer/timer_user_cooldown')
    
    assert response.status_code == 200
    data = response.json()
    assert data['can_post'] is False
    assert data['time_remaining'] > 0
    assert data['time_remaining'] <= 3600  # Should be less than 1 hour


def test_post_timer_prevents_double_post(client):
    """Test that timer prevents posting twice within cooldown."""
    post_data = {
        'image': 'https://example.com/test.jpg',
        'text': 'First post',
        'user': 'timer_user_double'
    }
    # First post should succeed
    response1 = client.post('/api/posts', json=post_data)
    assert response1.status_code == 201
    
    # Second post should fail with 429
    response2 = client.post('/api/posts', json=post_data)
    assert response2.status_code == 429
    assert 'wait' in response2.json()['detail'].lower()


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


def test_multiple_users_like_same_post(client):
    """Test multiple users liking the same post."""
    # Create a post
    post_data = {
        'image': 'https://example.com/test.jpg',
        'text': 'Test post',
        'user': 'post_author'
    }
    create_response = client.post('/api/posts', json=post_data)
    post_id = create_response.json()['id']
    
    # Multiple users like the post
    client.post(f'/api/posts/{post_id}/like?user=user1')
    client.post(f'/api/posts/{post_id}/like?user=user2')
    client.post(f'/api/posts/{post_id}/like?user=user3')
    
    # Get post and check like count
    response = client.get(f'/api/posts/{post_id}')
    data = response.json()
    
    assert data['likes_count'] == 3


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


def test_comment_on_nonexistent_post(client):
    """Test adding comment to non-existent post."""
    comment_data = {
        'user': 'commenter',
        'text': 'This should fail'
    }
    response = client.post('/api/posts/99999/comments', json=comment_data)
    
    assert response.status_code == 404


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


def test_tags_in_all_posts_response(client):
    """Test that tags are included when getting all posts."""
    # Create posts with tags
    post1 = {
        'image': 'https://example.com/post1.jpg',
        'text': 'Post 1 #tag1',
        'user': 'user1',
        'tags': ['tag1']
    }
    post2 = {
        'image': 'https://example.com/post2.jpg',
        'text': 'Post 2 #tag2',
        'user': 'user2',
        'tags': ['tag2']
    }
    
    client.post('/api/posts', json=post1)
    client.post('/api/posts', json=post2)
    
    # Get all posts
    response = client.get('/api/posts')
    data = response.json()
    
    # Check that all posts have tags field
    assert all('tags' in post for post in data)
    # Check that at least one post has tags
    assert any(len(post['tags']) > 0 for post in data)

