"""
Script to analyze sentiment for existing posts that don't have sentiment yet.
This script sends all posts without sentiment to the RabbitMQ queue for analysis.
"""
import os
import sys
import json
import pika
from database import Database

# Get RabbitMQ connection parameters from environment
rabbitmq_host = os.getenv('RABBITMQ_HOST', 'localhost')
rabbitmq_port = int(os.getenv('RABBITMQ_PORT', '5672'))
rabbitmq_user = os.getenv('RABBITMQ_USER', 'guest')
rabbitmq_password = os.getenv('RABBITMQ_PASSWORD', 'guest')

# Queue name
queue_name = 'sentiment_analysis_queue'

def analyze_existing_posts():
    """Send all posts without sentiment to the queue for analysis."""
    # Connect to database
    db = Database()
    
    # Get all posts
    posts = db.get_all_posts()
    
    # Filter posts without sentiment
    posts_to_analyze = []
    for post in posts:
        # Handle different tuple formats
        if len(post) >= 8:
            post_id, image, image_thumbnail, text, user, sentiment, sentiment_score, created_at = post[:8]
            if not sentiment:
                posts_to_analyze.append((post_id, text))
        elif len(post) >= 6:
            post_id, image, image_thumbnail, text, user, created_at = post[:6]
            posts_to_analyze.append((post_id, text))
        elif len(post) >= 5:
            post_id, image, text, user, created_at = post[:5]
            posts_to_analyze.append((post_id, text))
    
    if not posts_to_analyze:
        print("No posts need sentiment analysis.")
        return
    
    print(f"Found {len(posts_to_analyze)} posts without sentiment. Sending to queue...")
    
    # Connect to RabbitMQ
    try:
        credentials = pika.PlainCredentials(rabbitmq_user, rabbitmq_password)
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=rabbitmq_host,
                port=rabbitmq_port,
                credentials=credentials
            )
        )
        channel = connection.channel()
        
        # Declare queue
        channel.queue_declare(queue=queue_name, durable=True)
        
        # Send each post to queue
        for post_id, text in posts_to_analyze:
            message = {
                'post_id': post_id,
                'text': text
            }
            
            channel.basic_publish(
                exchange='',
                routing_key=queue_name,
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Make message persistent
                )
            )
            print(f"Sent post {post_id} to queue")
        
        connection.close()
        print(f"\nSuccessfully sent {len(posts_to_analyze)} posts to sentiment analysis queue.")
        print("The sentiment analysis service will process them and update the database.")
        
    except Exception as e:
        print(f"Error connecting to RabbitMQ: {e}")
        sys.exit(1)

if __name__ == '__main__':
    analyze_existing_posts()

