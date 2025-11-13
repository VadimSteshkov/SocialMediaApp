"""
Database module for social media posts.
Handles database initialization and operations for storing posts.
"""
import sqlite3
from datetime import datetime
from typing import Optional, List, Tuple


# Register datetime adapter for Python 3.12+ compatibility
def adapt_datetime_iso(val):
    """Adapt datetime to ISO format string."""
    return val.isoformat()


def convert_datetime(val):
    """Convert ISO format string to datetime."""
    if isinstance(val, bytes):
        val = val.decode()
    return datetime.fromisoformat(val)


# Register the adapter and converter
sqlite3.register_adapter(datetime, adapt_datetime_iso)
sqlite3.register_converter("timestamp", convert_datetime)


class Database:
    """Database handler for social media posts."""
    
    def __init__(self, db_path: str = "social_media.db"):
        """
        Initialize the database connection.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Create the posts table if it doesn't exist."""
        conn = sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image TEXT NOT NULL,
                text TEXT NOT NULL,
                user TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
    
    def insert_post(self, image: str, text: str, user: str) -> int:
        """
        Insert a new post into the database.
        If the database is empty, resets the ID counter to start from 1.
        
        Args:
            image: Path or URL to the image
            text: Post text/comment
            user: Username of the post author
            
        Returns:
            The ID of the inserted post
        """
        conn = sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES)
        cursor = conn.cursor()
        
        # Check if database is empty and reset ID counter if needed
        cursor.execute("SELECT COUNT(*) FROM posts")
        count = cursor.fetchone()[0]
        if count == 0:
            # Reset AUTOINCREMENT counter when database is empty
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='posts'")
        
        cursor.execute("""
            INSERT INTO posts (image, text, user, created_at)
            VALUES (?, ?, ?, ?)
        """, (image, text, user, datetime.now()))
        
        post_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return post_id
    
    def get_latest_post(self) -> Optional[Tuple[int, str, str, str, str]]:
        """
        Retrieve the latest post from the database.
        
        Returns:
            Tuple of (id, image, text, user, created_at) or None if no posts exist
        """
        conn = sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, image, text, user, created_at
            FROM posts
            ORDER BY created_at DESC
            LIMIT 1
        """)
        
        result = cursor.fetchone()
        conn.close()
        
        return result
    
    def get_all_posts(self) -> List[Tuple[int, str, str, str, str]]:
        """
        Retrieve all posts from the database.
        
        Returns:
            List of tuples containing (id, image, text, user, created_at)
        """
        conn = sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, image, text, user, created_at
            FROM posts
            ORDER BY created_at DESC
        """)
        
        results = cursor.fetchall()
        conn.close()
        
        return results
    
    def delete_all_posts(self):
        """Delete all posts from the database and reset the ID counter (useful for testing)."""
        conn = sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM posts")
        # Reset the AUTOINCREMENT counter
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='posts'")
        
        conn.commit()
        conn.close()

