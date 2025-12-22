"""
Database module for social media posts.
Handles database initialization and operations for storing posts.
Supports both SQLite and PostgreSQL databases.
"""
import os
import sqlite3
from datetime import datetime
from typing import Optional, List, Tuple

# Optional PostgreSQL support
try:
    import psycopg2
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False
    psycopg2 = None


# Register datetime adapter for Python 3.12+ compatibility (SQLite only)
def adapt_datetime_iso(val):
    """Adapt datetime to ISO format string."""
    return val.isoformat()


def convert_datetime(val):
    """Convert ISO format string to datetime."""
    if isinstance(val, bytes):
        val = val.decode()
    return datetime.fromisoformat(val)


# Register the adapter and converter for SQLite
sqlite3.register_adapter(datetime, adapt_datetime_iso)
sqlite3.register_converter("timestamp", convert_datetime)


class Database:
    """Database handler for social media posts. Supports SQLite and PostgreSQL."""
    
    def __init__(self, db_path: str = None):
        """
        Initialize the database connection.
        
        Args:
            db_path: Path to SQLite database file (if using SQLite).
                    If None, will use PostgreSQL if DB_HOST is set, otherwise SQLite.
        """
        # Determine database type from environment variables
        self.db_type = os.getenv('DB_TYPE', 'sqlite').lower()
        self.db_host = os.getenv('DB_HOST')
        self.db_port = os.getenv('DB_PORT', '5432')
        self.db_name = os.getenv('DB_NAME', 'social_media')
        self.db_user = os.getenv('DB_USER', 'postgres')
        self.db_password = os.getenv('DB_PASSWORD', 'postgres')
        
        # If DB_HOST is set, use PostgreSQL (if available)
        if self.db_host:
            if PSYCOPG2_AVAILABLE:
                self.db_type = 'postgresql'
            else:
                raise ImportError("PostgreSQL support requires psycopg2. Install it with: pip install psycopg2-binary")
        
        if self.db_type == 'postgresql':
            self.db_path = None
            self._init_postgres_connection()
        else:
            # SQLite fallback
            # Default to data/social_media.db for better organization
            default_path = os.getenv('DB_PATH', 'data/social_media.db')
            self.db_path = db_path or default_path
            # Ensure data directory exists
            if self.db_path and '/' in self.db_path:
                os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            self._init_sqlite_connection()
        
        self.init_database()
    
    def _init_postgres_connection(self):
        """Initialize PostgreSQL connection parameters."""
        self.conn_params = {
            'host': self.db_host,
            'port': self.db_port,
            'database': self.db_name,
            'user': self.db_user,
            'password': self.db_password
        }
    
    def _init_sqlite_connection(self):
        """Initialize SQLite connection (no-op, connection created per operation)."""
        pass
    
    def _get_connection(self):
        """Get a database connection based on the database type."""
        if self.db_type == 'postgresql':
            if not PSYCOPG2_AVAILABLE:
                raise ImportError("PostgreSQL support requires psycopg2. Install it with: pip install psycopg2-binary")
            return psycopg2.connect(**self.conn_params)
        else:
            return sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES, timeout=10.0)
    
    def _execute(self, query: str, params: tuple = None, fetch: bool = False):
        """
        Execute a query and return results if needed.
        
        Args:
            query: SQL query string
            params: Query parameters
            fetch: Whether to fetch results
            
        Returns:
            Query results if fetch=True, otherwise None
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            if fetch:
                results = cursor.fetchall()
                conn.commit()
                return results
            else:
                conn.commit()
                return cursor.lastrowid if hasattr(cursor, 'lastrowid') else None
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()
    
    def init_database(self):
        """Create the posts table and related tables if they don't exist."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            if self.db_type == 'postgresql':
                # PostgreSQL table definitions
                # Posts table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS posts (
                        id SERIAL PRIMARY KEY,
                        image TEXT NOT NULL,
                        image_thumbnail TEXT,
                        text TEXT NOT NULL,
                        "user" TEXT NOT NULL,
                        sentiment TEXT,
                        sentiment_score REAL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Add image_thumbnail column if it doesn't exist (for existing databases)
                cursor.execute("""
                    DO $$ 
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1 FROM information_schema.columns 
                            WHERE table_name='posts' AND column_name='image_thumbnail'
                        ) THEN
                            ALTER TABLE posts ADD COLUMN image_thumbnail TEXT;
                        END IF;
                    END $$;
                """)
                
                # Add sentiment columns if they don't exist
                cursor.execute("""
                    DO $$ 
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1 FROM information_schema.columns 
                            WHERE table_name='posts' AND column_name='sentiment'
                        ) THEN
                            ALTER TABLE posts ADD COLUMN sentiment TEXT;
                        END IF;
                        IF NOT EXISTS (
                            SELECT 1 FROM information_schema.columns 
                            WHERE table_name='posts' AND column_name='sentiment_score'
                        ) THEN
                            ALTER TABLE posts ADD COLUMN sentiment_score REAL;
                        END IF;
                    END $$;
                """)
                
                # User last post time table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS user_last_post (
                        "user" TEXT PRIMARY KEY,
                        last_post_time TIMESTAMP NOT NULL
                    )
                """)
                
                # Likes table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS likes (
                        id SERIAL PRIMARY KEY,
                        post_id INTEGER NOT NULL,
                        "user" TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(post_id, "user"),
                        FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE
                    )
                """)
                
                # Comments table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS comments (
                        id SERIAL PRIMARY KEY,
                        post_id INTEGER NOT NULL,
                        "user" TEXT NOT NULL,
                        text TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE
                    )
                """)
                
                # Tags table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS tags (
                        id SERIAL PRIMARY KEY,
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
                
                # Create indexes
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_likes_post_id ON likes(post_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_comments_post_id ON comments(post_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_post_tags_post_id ON post_tags(post_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_post_tags_tag_id ON post_tags(tag_id)")
            else:
                # SQLite table definitions
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image TEXT NOT NULL,
                image_thumbnail TEXT,
                text TEXT NOT NULL,
                user TEXT NOT NULL,
                sentiment TEXT,
                sentiment_score REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
                
                # Add image_thumbnail column if it doesn't exist (for existing databases)
                cursor.execute("""
                    PRAGMA table_info(posts)
                """)
                columns = [row[1] for row in cursor.fetchall()]
                if 'image_thumbnail' not in columns:
                    cursor.execute("""
                        ALTER TABLE posts ADD COLUMN image_thumbnail TEXT
                    """)
                if 'sentiment' not in columns:
                    cursor.execute("""
                        ALTER TABLE posts ADD COLUMN sentiment TEXT
                    """)
                if 'sentiment_score' not in columns:
                    cursor.execute("""
                        ALTER TABLE posts ADD COLUMN sentiment_score REAL
                    """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS user_last_post (
                        user TEXT PRIMARY KEY,
                        last_post_time TIMESTAMP NOT NULL
                    )
                """)
                
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
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS tags (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL UNIQUE
                    )
                """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS post_tags (
                        post_id INTEGER NOT NULL,
                        tag_id INTEGER NOT NULL,
                        PRIMARY KEY (post_id, tag_id),
                        FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
                        FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
                    )
                """)
                
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_likes_post_id ON likes(post_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_comments_post_id ON comments(post_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_post_tags_post_id ON post_tags(post_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_post_tags_tag_id ON post_tags(tag_id)")
            
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
        conn.close()
    
    def insert_post(self, image: str, text: str, user: str, image_thumbnail: Optional[str] = None) -> int:
        """
        Insert a new post into the database.
        Also updates the user's last post time.
        
        Args:
            image: Path or URL to the image
            text: Post text/comment
            user: Username of the post author
            image_thumbnail: Optional path or URL to the thumbnail image
            
        Returns:
            The ID of the inserted post
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            if self.db_type == 'postgresql':
                cursor.execute("""
                    INSERT INTO posts (image, image_thumbnail, text, "user", created_at)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                """, (image, image_thumbnail, text, user, datetime.now()))
                post_id = cursor.fetchone()[0]
                
                cursor.execute("""
                    INSERT INTO user_last_post ("user", last_post_time)
                    VALUES (%s, %s)
                    ON CONFLICT ("user") DO UPDATE SET last_post_time = EXCLUDED.last_post_time
                """, (user, datetime.now()))
            else:
                # SQLite
                cursor.execute("SELECT COUNT(*) FROM posts")
                count = cursor.fetchone()[0]
                if count == 0:
                    cursor.execute("DELETE FROM sqlite_sequence WHERE name='posts'")
                
                cursor.execute("""
                    INSERT INTO posts (image, image_thumbnail, text, user, created_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (image, image_thumbnail, text, user, datetime.now()))
                post_id = cursor.lastrowid
                
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
            cursor.close()
        conn.close()
    
    def update_post_thumbnail(self, post_id: int, image_thumbnail: str):
        """
        Update the thumbnail image for a post.
        
        Args:
            post_id: The ID of the post
            image_thumbnail: Path or URL to the thumbnail image
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            if self.db_type == 'postgresql':
                cursor.execute("""
                    UPDATE posts SET image_thumbnail = %s WHERE id = %s
                """, (image_thumbnail, post_id))
            else:
                cursor.execute("""
                    UPDATE posts SET image_thumbnail = ? WHERE id = ?
                """, (image_thumbnail, post_id))
            
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()
    
    def update_post_sentiment(self, post_id: int, sentiment: str, sentiment_score: float):
        """
        Update the sentiment analysis result for a post.
        
        Args:
            post_id: The ID of the post
            sentiment: Sentiment label (POSITIVE, NEGATIVE, NEUTRAL)
            sentiment_score: Sentiment confidence score (0.0 to 1.0)
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            if self.db_type == 'postgresql':
                cursor.execute("""
                    UPDATE posts SET sentiment = %s, sentiment_score = %s WHERE id = %s
                """, (sentiment, sentiment_score, post_id))
            else:
                cursor.execute("""
                    UPDATE posts SET sentiment = ?, sentiment_score = ? WHERE id = ?
                """, (sentiment, sentiment_score, post_id))
            
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()
    
    def get_latest_post(self) -> Optional[Tuple[int, str, Optional[str], str, str, Optional[str], Optional[float], str]]:
        """
        Retrieve the latest post from the database.
        
        Returns:
            Tuple of (id, image, image_thumbnail, text, user, sentiment, sentiment_score, created_at) or None if no posts exist
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if self.db_type == 'postgresql':
            query = """
                SELECT id, image, image_thumbnail, text, "user", sentiment, sentiment_score, created_at
                FROM posts
                ORDER BY created_at DESC
                LIMIT 1
            """
        else:
            query = """
            SELECT id, image, image_thumbnail, text, user, sentiment, sentiment_score, created_at
            FROM posts
            ORDER BY created_at DESC
            LIMIT 1
            """
        
        cursor.execute(query)
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        return result
    
    def get_all_posts(self) -> List[Tuple[int, str, Optional[str], str, str, Optional[str], Optional[float], str]]:
        """
        Retrieve all posts from the database.
        
        Returns:
            List of tuples containing (id, image, image_thumbnail, text, user, sentiment, sentiment_score, created_at)
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if self.db_type == 'postgresql':
            query = """
                SELECT id, image, image_thumbnail, text, "user", sentiment, sentiment_score, created_at
                FROM posts
                ORDER BY created_at DESC
            """
        else:
            query = """
            SELECT id, image, image_thumbnail, text, user, sentiment, sentiment_score, created_at
            FROM posts
            ORDER BY created_at DESC
            """
        
        cursor.execute(query)
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return results
    
    def get_post_by_id(self, post_id: int) -> Optional[Tuple[int, str, Optional[str], str, str, Optional[str], Optional[float], str]]:
        """
        Retrieve a post by its ID.
        
        Args:
            post_id: The ID of the post to retrieve
            
        Returns:
            Tuple of (id, image, image_thumbnail, text, user, sentiment, sentiment_score, created_at) or None if not found
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if self.db_type == 'postgresql':
            cursor.execute("""
                SELECT id, image, image_thumbnail, text, "user", sentiment, sentiment_score, created_at
                FROM posts
                WHERE id = %s
            """, (post_id,))
        else:
            cursor.execute("""
                SELECT id, image, image_thumbnail, text, user, sentiment, sentiment_score, created_at
                FROM posts
                WHERE id = ?
            """, (post_id,))
        
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        return result
    
    def search_posts_by_user(self, user: str) -> List[Tuple[int, str, Optional[str], str, str, Optional[str], Optional[float], str]]:
        """
        Search for posts by username.
        
        Args:
            user: Username to search for
            
        Returns:
            List of tuples containing (id, image, image_thumbnail, text, user, sentiment, sentiment_score, created_at)
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if self.db_type == 'postgresql':
            cursor.execute("""
                SELECT id, image, image_thumbnail, text, "user", sentiment, sentiment_score, created_at
                FROM posts
                WHERE "user" = %s
                ORDER BY created_at DESC
            """, (user,))
        else:
            cursor.execute("""
                SELECT id, image, image_thumbnail, text, user, sentiment, sentiment_score, created_at
                FROM posts
                WHERE user = ?
                ORDER BY created_at DESC
            """, (user,))
        
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return results
    
    def search_posts_by_text(self, text_query: str) -> List[Tuple[int, str, Optional[str], str, str, Optional[str], Optional[float], str]]:
        """
        Search for posts by text content (case-insensitive partial match).
        
        Args:
            text_query: Text to search for in post content
            
        Returns:
            List of tuples containing (id, image, image_thumbnail, text, user, sentiment, sentiment_score, created_at)
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if self.db_type == 'postgresql':
            cursor.execute("""
                SELECT id, image, image_thumbnail, text, "user", sentiment, sentiment_score, created_at
                FROM posts
                WHERE text ILIKE %s
                ORDER BY created_at DESC
            """, (f'%{text_query}%',))
        else:
            cursor.execute("""
                SELECT id, image, image_thumbnail, text, user, sentiment, sentiment_score, created_at
                FROM posts
                WHERE text LIKE ?
                ORDER BY created_at DESC
            """, (f'%{text_query}%',))
        
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return results
    
    def delete_all_posts(self):
        """Delete all posts from the database and reset the ID counter (useful for testing)."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("DELETE FROM posts")
            
            if self.db_type == 'sqlite':
                cursor.execute("DELETE FROM sqlite_sequence WHERE name='posts'")
            # PostgreSQL doesn't need sequence reset for SERIAL
            
            conn.commit()
        finally:
            cursor.close()
            conn.close()
    
    def get_user_last_post_time(self, user: str) -> Optional[datetime]:
        """
        Get the last post time for a user.
        
        Args:
            user: Username
            
        Returns:
            Last post time or None if user hasn't posted yet
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if self.db_type == 'postgresql':
            cursor.execute("""
                SELECT last_post_time FROM user_last_post WHERE "user" = %s
            """, (user,))
        else:
            cursor.execute("""
                SELECT last_post_time FROM user_last_post WHERE user = ?
            """, (user,))
        
        result = cursor.fetchone()
        cursor.close()
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
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            if self.db_type == 'postgresql':
                cursor.execute("""
                    INSERT INTO likes (post_id, "user", created_at)
                    VALUES (%s, %s, %s)
                """, (post_id, user, datetime.now()))
                conn.commit()
                cursor.close()
                conn.close()
                return True
            else:
                cursor.execute("""
                    INSERT INTO likes (post_id, user, created_at)
                    VALUES (?, ?, ?)
                """, (post_id, user, datetime.now()))
                conn.commit()
                cursor.close()
                conn.close()
                return True
        except (psycopg2.IntegrityError, sqlite3.IntegrityError):
            # Already liked
            conn.rollback()
            cursor.close()
            conn.close()
            return False
    
    def remove_like(self, post_id: int, user: str):
        """
        Remove a like from a post.
        
        Args:
            post_id: ID of the post
            user: Username who unliked the post
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if self.db_type == 'postgresql':
            cursor.execute("""
                DELETE FROM likes WHERE post_id = %s AND "user" = %s
            """, (post_id, user))
        else:
            cursor.execute("""
                DELETE FROM likes WHERE post_id = ? AND user = ?
            """, (post_id, user))
        
        conn.commit()
        cursor.close()
        conn.close()
    
    def get_like_count(self, post_id: int) -> int:
        """
        Get the number of likes for a post.
        
        Args:
            post_id: ID of the post
            
        Returns:
            Number of likes
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if self.db_type == 'postgresql':
            cursor.execute("""
                SELECT COUNT(*) FROM likes WHERE post_id = %s
            """, (post_id,))
        else:
            cursor.execute("""
                SELECT COUNT(*) FROM likes WHERE post_id = ?
            """, (post_id,))
        
        count = cursor.fetchone()[0]
        cursor.close()
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
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if self.db_type == 'postgresql':
            cursor.execute("""
                SELECT COUNT(*) FROM likes WHERE post_id = %s AND "user" = %s
            """, (post_id, user))
        else:
            cursor.execute("""
                SELECT COUNT(*) FROM likes WHERE post_id = ? AND user = ?
            """, (post_id, user))
        
        count = cursor.fetchone()[0]
        cursor.close()
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
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if self.db_type == 'postgresql':
            cursor.execute("""
                INSERT INTO comments (post_id, "user", text, created_at)
                VALUES (%s, %s, %s, %s)
                RETURNING id
            """, (post_id, user, text, datetime.now()))
            comment_id = cursor.fetchone()[0]
        else:
            cursor.execute("""
                INSERT INTO comments (post_id, user, text, created_at)
                VALUES (?, ?, ?, ?)
            """, (post_id, user, text, datetime.now()))
            comment_id = cursor.lastrowid
        
        conn.commit()
        cursor.close()
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
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if self.db_type == 'postgresql':
            cursor.execute("""
                SELECT id, "user", text, created_at
                FROM comments
                WHERE post_id = %s
                ORDER BY created_at ASC
            """, (post_id,))
        else:
            cursor.execute("""
                SELECT id, user, text, created_at
                FROM comments
                WHERE post_id = ?
                ORDER BY created_at ASC
            """, (post_id,))
        
        results = cursor.fetchall()
        cursor.close()
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
        conn = self._get_connection()
        cursor = conn.cursor()
        
        tag_normalized = tag_name.lower()
        
        if self.db_type == 'postgresql':
            cursor.execute("SELECT id FROM tags WHERE name = %s", (tag_normalized,))
        else:
            cursor.execute("SELECT id FROM tags WHERE name = ?", (tag_normalized,))
        
        result = cursor.fetchone()
        
        if result:
            tag_id = result[0]
        else:
            if self.db_type == 'postgresql':
                cursor.execute("INSERT INTO tags (name) VALUES (%s) RETURNING id", (tag_normalized,))
                tag_id = cursor.fetchone()[0]
            else:
                cursor.execute("INSERT INTO tags (name) VALUES (?)", (tag_normalized,))
                tag_id = cursor.lastrowid
        
        conn.commit()
        cursor.close()
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
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            for tag_name in tags:
                if not tag_name or not tag_name.strip():
                    continue
                    
                tag_normalized = tag_name.strip().lower()
                
                if self.db_type == 'postgresql':
                    cursor.execute("SELECT id FROM tags WHERE name = %s", (tag_normalized,))
                else:
                    cursor.execute("SELECT id FROM tags WHERE name = ?", (tag_normalized,))
                
                result = cursor.fetchone()
                
                if result:
                    tag_id = result[0]
                else:
                    if self.db_type == 'postgresql':
                        cursor.execute("INSERT INTO tags (name) VALUES (%s) RETURNING id", (tag_normalized,))
                        tag_id = cursor.fetchone()[0]
                    else:
                        cursor.execute("INSERT INTO tags (name) VALUES (?)", (tag_normalized,))
                        tag_id = cursor.lastrowid
                
                # Link tag to post
                try:
                    if self.db_type == 'postgresql':
                        cursor.execute("""
                            INSERT INTO post_tags (post_id, tag_id)
                            VALUES (%s, %s)
                        """, (post_id, tag_id))
                    else:
                        cursor.execute("""
                            INSERT INTO post_tags (post_id, tag_id)
                            VALUES (?, ?)
                        """, (post_id, tag_id))
                except (psycopg2.IntegrityError, sqlite3.IntegrityError):
                    # Tag already associated with post
                    pass
            
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()
    
    def get_post_tags(self, post_id: int) -> List[str]:
        """
        Get all tags for a post.
        
        Args:
            post_id: ID of the post
            
        Returns:
            List of tag names
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if self.db_type == 'postgresql':
            cursor.execute("""
                SELECT t.name
                FROM tags t
                JOIN post_tags pt ON t.id = pt.tag_id
                WHERE pt.post_id = %s
                ORDER BY t.name
            """, (post_id,))
        else:
            cursor.execute("""
                SELECT t.name
                FROM tags t
                JOIN post_tags pt ON t.id = pt.tag_id
                WHERE pt.post_id = ?
                ORDER BY t.name
            """, (post_id,))
        
        results = cursor.fetchall()
        cursor.close()
        conn.close()

        return [row[0] for row in results]
    
    def search_posts_by_tag(self, tag: str) -> List[Tuple[int, str, Optional[str], str, str, Optional[str], Optional[float], str]]:
        """
        Search for posts by tag.
        
        Args:
            tag: Tag name to search for
            
        Returns:
            List of tuples containing (id, image, image_thumbnail, text, user, sentiment, sentiment_score, created_at)
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        tag_normalized = tag.strip().lower()
        
        if self.db_type == 'postgresql':
            cursor.execute("""
                SELECT DISTINCT p.id, p.image, p.image_thumbnail, p.text, p."user", p.sentiment, p.sentiment_score, p.created_at
                FROM posts p
                JOIN post_tags pt ON p.id = pt.post_id
                JOIN tags t ON pt.tag_id = t.id
                WHERE t.name = %s
                ORDER BY p.created_at DESC
            """, (tag_normalized,))
        else:
            cursor.execute("""
                SELECT DISTINCT p.id, p.image, p.image_thumbnail, p.text, p.user, p.sentiment, p.sentiment_score, p.created_at
                FROM posts p
                JOIN post_tags pt ON p.id = pt.post_id
                JOIN tags t ON pt.tag_id = t.id
                WHERE t.name = ?
                ORDER BY p.created_at DESC
            """, (tag_normalized,))
        
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return results
