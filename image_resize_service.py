"""
Image Resize Microservice
Listens to RabbitMQ queue and processes image resizing tasks.
"""
import os
import json
import pika
from PIL import Image
from pathlib import Path
from database import Database
import sys

# Configuration
RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'localhost')
RABBITMQ_PORT = int(os.getenv('RABBITMQ_PORT', '5672'))
RABBITMQ_USER = os.getenv('RABBITMQ_USER', 'guest')
RABBITMQ_PASSWORD = os.getenv('RABBITMQ_PASSWORD', 'guest')
QUEUE_NAME = 'image_resize_queue'

# Database configuration
DB_TYPE = os.getenv('DB_TYPE', 'postgresql')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'social_media')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'postgres')

# Image processing configuration
THUMBNAIL_SIZE = (1200, 1200)  # Max width and height in pixels
UPLOAD_DIR = Path("/app/uploads")
THUMBNAIL_DIR = UPLOAD_DIR / "thumbnails"
FULL_DIR = UPLOAD_DIR / "full"

# Create thumbnail directory if it doesn't exist
THUMBNAIL_DIR.mkdir(parents=True, exist_ok=True)


def resize_image(input_path: str, output_path: str, size: tuple = THUMBNAIL_SIZE):
    """
    Resize an image to thumbnail size while maintaining aspect ratio.
    
    Args:
        input_path: Path to the input image
        output_path: Path to save the resized image
        size: Tuple of (max_width, max_height)
    """
    try:
        # Open image
        with Image.open(input_path) as img:
            # Convert to RGB if necessary (handles PNG with transparency, etc.)
            if img.mode in ('RGBA', 'LA', 'P'):
                # Create a white background
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Calculate thumbnail size maintaining aspect ratio
            img.thumbnail(size, Image.Resampling.LANCZOS)
            
            # Save thumbnail
            img.save(output_path, 'JPEG', quality=85, optimize=True)
            
            return True
    except Exception as e:
        print(f"Error resizing image {input_path}: {e}", file=sys.stderr)
        return False


def process_image_message(ch, method, properties, body):
    """
    Process a message from the queue.
    
    Args:
        ch: Channel
        method: Method
        properties: Properties
        body: Message body (JSON string)
    """
    try:
        # Parse message
        message = json.loads(body)
        post_id = message.get('post_id')
        image_path = message.get('image_path')
        
        if not post_id or not image_path:
            print(f"Invalid message: missing post_id or image_path", file=sys.stderr)
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return
        
        print(f"Processing image for post {post_id}: {image_path}")
        
        # Convert image_path to absolute path if needed
        # image_path might be a URL path like "/uploads/full/filename.jpg"
        # or an absolute file path
        if image_path.startswith('/uploads/'):
            # It's a URL path, convert to file path
            # Remove leading /uploads/ and use FULL_DIR
            relative_path = image_path.replace('/uploads/full/', '').replace('/uploads/thumbnails/', '')
            image_path = FULL_DIR / relative_path
        elif not os.path.isabs(image_path):
            # If relative, assume it's in the uploads directory
            image_path = FULL_DIR / Path(image_path).name
        
        # Check if file exists
        if not os.path.exists(image_path):
            print(f"Image file not found: {image_path}", file=sys.stderr)
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return
        
        # Generate thumbnail filename
        image_filename = Path(image_path).name
        thumbnail_filename = f"thumb_{image_filename}"
        thumbnail_path = THUMBNAIL_DIR / thumbnail_filename
        
        # Resize image
        success = resize_image(str(image_path), str(thumbnail_path))
        
        if not success:
            print(f"Failed to resize image for post {post_id}", file=sys.stderr)
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return
        
        # Update database with thumbnail path
        thumbnail_url = f"/uploads/thumbnails/{thumbnail_filename}"
        
        db = Database()
        db.update_post_thumbnail(post_id, thumbnail_url)
        
        print(f"Successfully created thumbnail for post {post_id}: {thumbnail_url}")
        
        # Acknowledge message
        ch.basic_ack(delivery_tag=method.delivery_tag)
        
    except json.JSONDecodeError as e:
        print(f"Error parsing message: {e}", file=sys.stderr)
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        print(f"Error processing message: {e}", file=sys.stderr)
        # Acknowledge to prevent infinite retries (in production, might want retry logic)
        ch.basic_ack(delivery_tag=method.delivery_tag)


def main():
    """Main function to start the image resize service."""
    print("Starting Image Resize Microservice...")
    print(f"Connecting to RabbitMQ at {RABBITMQ_HOST}:{RABBITMQ_PORT}")
    
    try:
        # Create connection
        credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=RABBITMQ_HOST,
                port=RABBITMQ_PORT,
                credentials=credentials
            )
        )
        channel = connection.channel()
        
        # Declare queue (idempotent)
        channel.queue_declare(queue=QUEUE_NAME, durable=True)
        
        # Set QoS to process one message at a time
        channel.basic_qos(prefetch_count=1)
        
        # Set up consumer
        channel.basic_consume(
            queue=QUEUE_NAME,
            on_message_callback=process_image_message
        )
        
        print(f"Waiting for messages in queue '{QUEUE_NAME}'. To exit press CTRL+C")
        channel.start_consuming()
        
    except KeyboardInterrupt:
        print("\nStopping Image Resize Microservice...")
        if 'connection' in locals() and connection.is_open:
            connection.close()
    except Exception as e:
        import traceback
        print(f"Error in main loop: {e}", file=sys.stderr)
        print(f"Traceback: {traceback.format_exc()}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

