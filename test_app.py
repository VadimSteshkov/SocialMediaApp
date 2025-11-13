"""
Test suite for the social media app.
Tests database operations and post retrieval.
"""
import unittest
import os
from database import Database


class TestSocialMediaApp(unittest.TestCase):
    """Test cases for the social media application."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Use a test database
        self.test_db_path = "test_social_media.db"
        self.db = Database(db_path=self.test_db_path)
        # Clear any existing data
        self.db.delete_all_posts()
    
    def tearDown(self):
        """Clean up after each test method."""
        # Remove test database file
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
    
    def test_insert_post(self):
        """Test inserting a post into the database."""
        post_id = self.db.insert_post(
            image="https://example.com/test.jpg",
            text="Test post",
            user="test_user"
        )
        
        self.assertIsNotNone(post_id)
        self.assertIsInstance(post_id, int)
        self.assertGreater(post_id, 0)
    
    def test_get_latest_post(self):
        """Test retrieving the latest post."""
        # Insert multiple posts
        self.db.insert_post(
            image="https://example.com/first.jpg",
            text="First post",
            user="user1"
        )
        
        self.db.insert_post(
            image="https://example.com/second.jpg",
            text="Second post",
            user="user2"
        )
        
        self.db.insert_post(
            image="https://example.com/third.jpg",
            text="Third post",
            user="user3"
        )
        
        # Get latest post
        latest = self.db.get_latest_post()
        
        self.assertIsNotNone(latest)
        post_id, image, text, user, created_at = latest
        
        # Latest post should be the third one
        self.assertEqual(text, "Third post")
        self.assertEqual(user, "user3")
        self.assertEqual(image, "https://example.com/third.jpg")
    
    def test_get_latest_post_empty_database(self):
        """Test retrieving latest post from empty database."""
        latest = self.db.get_latest_post()
        self.assertIsNone(latest)
    
    def test_get_all_posts(self):
        """Test retrieving all posts."""
        # Insert multiple posts
        self.db.insert_post(
            image="https://example.com/post1.jpg",
            text="Post 1",
            user="user1"
        )
        self.db.insert_post(
            image="https://example.com/post2.jpg",
            text="Post 2",
            user="user2"
        )
        
        all_posts = self.db.get_all_posts()
        
        self.assertEqual(len(all_posts), 2)
        self.assertEqual(all_posts[0][2], "Post 2")  # Latest first
        self.assertEqual(all_posts[1][2], "Post 1")
    
    def test_post_fields(self):
        """Test that all required fields are stored correctly."""
        self.db.insert_post(
            image="https://example.com/image.jpg",
            text="Test comment",
            user="testuser"
        )
        
        latest = self.db.get_latest_post()
        self.assertIsNotNone(latest)
        
        post_id, image, text, user, created_at = latest
        
        self.assertEqual(image, "https://example.com/image.jpg")
        self.assertEqual(text, "Test comment")
        self.assertEqual(user, "testuser")
        self.assertIsNotNone(created_at)


if __name__ == "__main__":
    # Run with unittest for basic output
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--pytest":
        # If pytest is requested, use it
        import pytest
        pytest.main([__file__, "-v", "--tb=short"])
    else:
        # Default: use unittest with verbose output
        unittest.main(verbosity=2)

