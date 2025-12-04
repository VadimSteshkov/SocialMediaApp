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
        """Create the posts table and related tables if they don't exist."""
        conn = sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES, timeout=10.0)
        cursor = conn.cursor()
        
        # Posts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image TEXT NOT NULL,
                text TEXT NOT NULL,
                user TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # User last post time table (for timer functionality)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_last_post (
                user TEXT PRIMARY KEY,
                last_post_time TIMESTAMP NOT NULL
            )
        """)
        
        # Likes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS likes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id INTEGER NOT NULL,
                user TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(post_id, user),
                FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE
            )
        """)
        
        # Comments table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id INTEGER NOT NULL,
                user TEXT NOT NULL,
                text TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE
            )
        """)
        
        # Tags table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            )
        """)
        
        # Post tags junction table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS post_tags (
                post_id INTEGER NOT NULL,
                tag_id INTEGER NOT NULL,
                PRIMARY KEY (post_id, tag_id),
                FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
                FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
            )
        """)
        
        # Create indexes for better performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_likes_post_id ON likes(post_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_comments_post_id ON comments(post_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_post_tags_post_id ON post_tags(post_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_post_tags_tag_id ON post_tags(tag_id)")
        
        conn.commit()
        conn.close()
    
    def insert_post(self, image: str, text: str, user: str) -> int:
        """
        Insert a new post into the database.
        If the database is empty, resets the ID counter to start from 1.
        Also updates the user's last post time.
        
        Args:
            image: Path or URL to the image
            text: Post text/comment
            user: Username of the post author
            
        Returns:
            The ID of the inserted post
        """
        conn = sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES, timeout=10.0)
        cursor = conn.cursor()
        
        try:
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
            
            # Update user's last post time in the same transaction
            cursor.execute("""
                INSERT OR REPLACE INTO user_last_post (user, last_post_time)
                VALUES (?, ?)
            """, (user, datetime.now()))
            
            conn.commit()
            return post_id
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
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
    
    def get_post_by_id(self, post_id: int) -> Optional[Tuple[int, str, str, str, str]]:
        """
        Retrieve a post by its ID.
        
        Args:
            post_id: The ID of the post to retrieve
            
        Returns:
            Tuple of (id, image, text, user, created_at) or None if not found
        """
        conn = sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, image, text, user, created_at
            FROM posts
            WHERE id = ?
        """, (post_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        return result
    
    def search_posts_by_user(self, user: str) -> List[Tuple[int, str, str, str, str]]:
        """
        Search for posts by username.
        
        Args:
            user: Username to search for
            
        Returns:
            List of tuples containing (id, image, text, user, created_at)
        """
        conn = sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, image, text, user, created_at
            FROM posts
            WHERE user = ?
            ORDER BY created_at DESC
        """, (user,))
        
        results = cursor.fetchall()
        conn.close()
        
        return results
    
    def search_posts_by_text(self, text_query: str) -> List[Tuple[int, str, str, str, str]]:
        """
        Search for posts by text content (case-insensitive partial match).
        
        Args:
            text_query: Text to search for in post content
            
        Returns:
            List of tuples containing (id, image, text, user, created_at)
        """
        conn = sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, image, text, user, created_at
            FROM posts
            WHERE text LIKE ?
            ORDER BY created_at DESC
        """, (f'%{text_query}%',))
        
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
    
    def get_user_last_post_time(self, user: str) -> Optional[datetime]:
        """
        Get the last post time for a user.
        
        Args:
            user: Username
            
        Returns:
            Last post time or None if user hasn't posted yet
        """
        conn = sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT last_post_time FROM user_last_post WHERE user = ?
        """, (user,))
        
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else None
    
    def update_user_last_post_time(self, user: str):
        """
        Update the last post time for a user.
        NOTE: This is now done in insert_post to avoid database locks.
        This method is kept for backward compatibility but does nothing.
        
        Args:
            user: Username
        """
        # This is now handled in insert_post to avoid database locks
        pass
    
    def add_like(self, post_id: int, user: str) -> bool:
        """
        Add a like to a post.
        
        Args:
            post_id: ID of the post
            user: Username who liked the post
            
        Returns:
            True if like was added, False if already liked
        """
        conn = sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO likes (post_id, user, created_at)
                VALUES (?, ?, ?)
            """, (post_id, user, datetime.now()))
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            # Already liked
            conn.close()
            return False
    
    def remove_like(self, post_id: int, user: str):
        """
        Remove a like from a post.
        
        Args:
            post_id: ID of the post
            user: Username who unliked the post
        """
        conn = sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES)
        cursor = conn.cursor()
        
        cursor.execute("""
            DELETE FROM likes WHERE post_id = ? AND user = ?
        """, (post_id, user))
        
        conn.commit()
        conn.close()
    
    def get_like_count(self, post_id: int) -> int:
        """
        Get the number of likes for a post.
        
        Args:
            post_id: ID of the post
            
        Returns:
            Number of likes
        """
        conn = sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT COUNT(*) FROM likes WHERE post_id = ?
        """, (post_id,))
        
        count = cursor.fetchone()[0]
        conn.close()
        
        return count
    
    def is_liked_by_user(self, post_id: int, user: str) -> bool:
        """
        Check if a post is liked by a user.
        
        Args:
            post_id: ID of the post
            user: Username
            
        Returns:
            True if liked, False otherwise
        """
        conn = sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT COUNT(*) FROM likes WHERE post_id = ? AND user = ?
        """, (post_id, user))
        
        count = cursor.fetchone()[0]
        conn.close()
        
        return count > 0
    
    def add_comment(self, post_id: int, user: str, text: str) -> int:
        """
        Add a comment to a post.
        
        Args:
            post_id: ID of the post
            user: Username who commented
            text: Comment text
            
        Returns:
            ID of the created comment
        """
        conn = sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO comments (post_id, user, text, created_at)
            VALUES (?, ?, ?, ?)
        """, (post_id, user, text, datetime.now()))
        
        comment_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return comment_id
    
    def get_comments(self, post_id: int) -> List[Tuple[int, str, str, datetime]]:
        """
        Get all comments for a post.
        
        Args:
            post_id: ID of the post
            
        Returns:
            List of tuples containing (id, user, text, created_at)
        """
        conn = sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, user, text, created_at
            FROM comments
            WHERE post_id = ?
            ORDER BY created_at ASC
        """, (post_id,))
        
        results = cursor.fetchall()
        conn.close()
        
        return results
    
    def get_or_create_tag(self, tag_name: str) -> int:
        """
        Get or create a tag and return its ID.
        
        Args:
            tag_name: Name of the tag
            
        Returns:
            Tag ID
        """
        conn = sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES)
        cursor = conn.cursor()
        
        # Try to get existing tag
        cursor.execute("SELECT id FROM tags WHERE name = ?", (tag_name.lower(),))
        result = cursor.fetchone()
        
        if result:
            tag_id = result[0]
        else:
            # Create new tag
            cursor.execute("INSERT INTO tags (name) VALUES (?)", (tag_name.lower(),))
            tag_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        return tag_id
    
    def add_tags_to_post(self, post_id: int, tags: List[str]):
        """
        Add tags to a post.
        
        Args:
            post_id: ID of the post
            tags: List of tag names
        """
        if not tags:
            return
        
        conn = sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES, timeout=10.0)
        cursor = conn.cursor()
        
        try:
            for tag_name in tags:
                if not tag_name or not tag_name.strip():
                    continue
                    
                tag_normalized = tag_name.strip().lower()
                
                # Get or create tag within the same connection
                cursor.execute("SELECT id FROM tags WHERE name = ?", (tag_normalized,))
                result = cursor.fetchone()
                
                if result:
                    tag_id = result[0]
                else:
                    cursor.execute("INSERT INTO tags (name) VALUES (?)", (tag_normalized,))
                    tag_id = cursor.lastrowid
                
                # Link tag to post
                try:
                    cursor.execute("""
                        INSERT INTO post_tags (post_id, tag_id)
                        VALUES (?, ?)
                    """, (post_id, tag_id))
                except sqlite3.IntegrityError:
                    # Tag already associated with post
                    pass
            
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def get_post_tags(self, post_id: int) -> List[str]:
        """
        Get all tags for a post.
        
        Args:
            post_id: ID of the post
            
        Returns:
            List of tag names
        """
        conn = sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT t.name
            FROM tags t
            JOIN post_tags pt ON t.id = pt.tag_id
            WHERE pt.post_id = ?
            ORDER BY t.name
        """, (post_id,))
        
        results = cursor.fetchall()
        conn.close()
        
        return [row[0] for row in results]
    
    def search_posts_by_tag(self, tag: str) -> List[Tuple[int, str, str, str, str]]:
        """
        Search for posts by tag.
        
        Args:
            tag: Tag name to search for
            
        Returns:
            List of tuples containing (id, image, text, user, created_at)
        """
        conn = sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES)
        cursor = conn.cursor()
        
        # Normalize tag to lowercase (tags are stored in lowercase)
        tag_normalized = tag.strip().lower()
        
        cursor.execute("""
            SELECT DISTINCT p.id, p.image, p.text, p.user, p.created_at
            FROM posts p
            JOIN post_tags pt ON p.id = pt.post_id
            JOIN tags t ON pt.tag_id = t.id
            WHERE t.name = ?
            ORDER BY p.created_at DESC
        """, (tag_normalized,))
        
        results = cursor.fetchall()
        conn.close()
        
        return results

