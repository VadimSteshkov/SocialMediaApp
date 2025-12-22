"""
Sentiment Analysis Microservice using pre-trained model.
Listens to RabbitMQ queue and analyzes sentiment of post text.
"""
import os
import sys
import json
import logging
import pika
from transformers import pipeline

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'rabbitmq')
RABBITMQ_PORT = int(os.getenv('RABBITMQ_PORT', 5672))
RABBITMQ_USER = os.getenv('RABBITMQ_USER', 'guest')
RABBITMQ_PASSWORD = os.getenv('RABBITMQ_PASSWORD', 'guest')
SENTIMENT_QUEUE = 'sentiment_analysis_queue'

# Sentiment Analysis Model
_sentiment_analyzer = None


def load_sentiment_model():
    """Load sentiment analysis model once."""
    global _sentiment_analyzer
    if _sentiment_analyzer is None:
        logger.info("Loading sentiment analysis model...")
        try:
            # Using cardiffnlp/twitter-roberta-base-sentiment for better social media text analysis
            _sentiment_analyzer = pipeline(
                "sentiment-analysis",
                model="cardiffnlp/twitter-roberta-base-sentiment",
                tokenizer="cardiffnlp/twitter-roberta-base-sentiment"
            )
            logger.info("Sentiment analysis model loaded successfully")
        except Exception as e:
            logger.error(f"Error loading sentiment model: {e}")
            raise
    return _sentiment_analyzer


def analyze_sentiment(text: str) -> dict:
    """
    Analyze sentiment of text.
    
    Args:
        text: Text to analyze
        
    Returns:
        Dictionary with sentiment label and score
    """
    try:
        analyzer = load_sentiment_model()
        
        if not text or not text.strip():
            return {'label': 'NEUTRAL', 'score': 0.5}
        
        logger.info(f"Analyzing sentiment for text: '{text[:50]}...'")
        
        # Analyze sentiment
        result = analyzer(text)[0]
        
        # Map labels to our format
        label_mapping = {
            'LABEL_0': 'NEGATIVE',
            'LABEL_1': 'NEUTRAL',
            'LABEL_2': 'POSITIVE'
        }
        
        label = label_mapping.get(result['label'], 'NEUTRAL')
        score = result['score']
        
        logger.info(f"Sentiment: {label} (score: {score:.2f})")
        
        return {
            'label': label,
            'score': float(score)
        }
        
    except Exception as e:
        logger.error(f"Error analyzing sentiment: {e}")
        return {'label': 'NEUTRAL', 'score': 0.5}


def process_sentiment_message(ch, method, properties, body):
    """Process sentiment analysis request from RabbitMQ queue."""
    try:
        # Parse message
        message = json.loads(body.decode('utf-8'))
        post_id = message.get('post_id')
        text = message.get('text', '')
        
        logger.info(f"Processing sentiment analysis for post_id: {post_id}")
        
        # Analyze sentiment
        sentiment_result = analyze_sentiment(text)
        
        # Update database
        try:
            import database
            db = database.Database()
            db.update_post_sentiment(post_id, sentiment_result['label'], sentiment_result['score'])
            logger.info(f"Updated post {post_id} with sentiment: {sentiment_result['label']}")
        except Exception as e:
            logger.error(f"Error updating database: {e}")
            raise
        
        ch.basic_ack(delivery_tag=method.delivery_tag)
        
    except Exception as e:
        logger.error(f"Error processing sentiment message: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def main():
    """Main function to start the sentiment analysis microservice."""
    try:
        logger.info("Starting Sentiment Analysis Microservice...")
        
        # Load model
        load_sentiment_model()
        
        # Connect to RabbitMQ
        credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=RABBITMQ_HOST,
                port=RABBITMQ_PORT,
                credentials=credentials
            )
        )
        channel = connection.channel()
        
        # Declare queue
        channel.queue_declare(queue=SENTIMENT_QUEUE, durable=True)
        
        # Set up consumer
        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(
            queue=SENTIMENT_QUEUE,
            on_message_callback=process_sentiment_message
        )
        
        logger.info(f"Sentiment Analysis Microservice started. Waiting for messages on queue '{SENTIMENT_QUEUE}'...")
        channel.start_consuming()
        
    except KeyboardInterrupt:
        logger.info("Stopping Sentiment Analysis Microservice...")
        if 'connection' in locals():
            connection.close()
    except Exception as e:
        logger.error(f"Failed to start Sentiment Analysis Microservice: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()

