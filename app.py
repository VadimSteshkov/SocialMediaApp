"""
Main application for the social media app.
Defines sample posts and demonstrates database operations.
"""
from database import Database


def main():
    """Main function to create sample posts and retrieve the latest one."""
    # Initialize database
    db = Database()
    
    # Define 3 sample posts
    posts = [
        {
            "image": "https://example.com/images/sunset.jpg",
            "text": "Beautiful sunset at the beach today!",
            "user": "alice_smith"
        },
        {
            "image": "https://example.com/images/coffee.jpg",
            "text": "Morning coffee and coding session",
            "user": "bob_jones"
        },
        {
            "image": "https://example.com/images/mountain.jpg",
            "text": "Hiking adventure in the mountains!",
            "user": "charlie_brown"
        }
    ]
    
    # Store posts in database
    print("Storing posts in database...")
    for post in posts:
        post_id = db.insert_post(
            image=post["image"],
            text=post["text"],
            user=post["user"]
        )
        print(f"✓ Post {post_id} created by {post['user']}")
    
    # Retrieve the latest post
    print("\nRetrieving the latest post...")
    latest_post = db.get_latest_post()
    
    if latest_post:
        # Handle both old format (5 elements) and new format (6 elements)
        if len(latest_post) == 5:
            post_id, image, text, user, created_at = latest_post
            image_thumbnail = None
        else:
            post_id, image, image_thumbnail, text, user, created_at = latest_post
        print(f"\nLatest Post:")
        print(f"  ID: {post_id}")
        print(f"  User: {user}")
        print(f"  Text: {text}")
        print(f"  Image: {image}")
        if image_thumbnail:
            print(f"  Thumbnail: {image_thumbnail}")
        print(f"  Created at: {created_at}")
    else:
        print("No posts found in the database.")


if __name__ == "__main__":
    main()

