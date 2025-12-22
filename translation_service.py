"""
Translation Microservice using pre-trained translation models.
Listens to RabbitMQ queue and translates post text.
"""
import os
import sys
import json
import logging
import pika
from transformers import MarianMTModel, MarianTokenizer

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'rabbitmq')
RABBITMQ_PORT = int(os.getenv('RABBITMQ_PORT', '5672'))
RABBITMQ_USER = os.getenv('RABBITMQ_USER', 'guest')
RABBITMQ_PASSWORD = os.getenv('RABBITMQ_PASSWORD', 'guest')
TRANSLATION_QUEUE = 'translation_queue'
TRANSLATION_RESPONSE_QUEUE = 'translation_response_queue'

# Translation Models
_models = {}
_tokenizers = {}

# Supported language pairs
# Using Helsinki-NLP models for English <-> Russian
SUPPORTED_LANGUAGES = {
    'en': 'English',
    'ru': 'Russian',
    'de': 'German',
    'es': 'Spanish',
    'fr': 'French'
}

# Model mapping for language pairs
MODEL_MAPPING = {
    'en-ru': 'Helsinki-NLP/opus-mt-en-ru',
    'ru-en': 'Helsinki-NLP/opus-mt-ru-en',
    'en-de': 'Helsinki-NLP/opus-mt-en-de',
    'de-en': 'Helsinki-NLP/opus-mt-de-en',
    'en-es': 'Helsinki-NLP/opus-mt-en-es',
    'es-en': 'Helsinki-NLP/opus-mt-es-en',
    'en-fr': 'Helsinki-NLP/opus-mt-en-fr',
    'fr-en': 'Helsinki-NLP/opus-mt-fr-en',
}


def load_translation_model(source_lang: str, target_lang: str):
    """Load translation model for a language pair."""
    model_key = f"{source_lang}-{target_lang}"
    
    if model_key not in _models:
        model_name = MODEL_MAPPING.get(model_key)
        if not model_name:
            # Fallback: try to find reverse model
            reverse_key = f"{target_lang}-{source_lang}"
            if reverse_key in MODEL_MAPPING:
                logger.warning(f"Model {model_key} not found, using reverse translation")
                return None
            else:
                logger.error(f"No model found for {model_key}")
                return None
        
        logger.info(f"Loading translation model: {model_name}")
        try:
            _tokenizers[model_key] = MarianTokenizer.from_pretrained(model_name)
            _models[model_key] = MarianMTModel.from_pretrained(model_name)
            logger.info(f"Translation model {model_name} loaded successfully")
        except Exception as e:
            logger.error(f"Error loading translation model: {e}")
            return None
    
    return _models[model_key], _tokenizers[model_key]


def detect_language(text: str) -> str:
    """
    Simple language detection based on character analysis.
    For production, use a proper language detection library.
    """
    # Simple heuristic: check for Cyrillic characters
    if any('\u0400' <= char <= '\u04FF' for char in text):
        return 'ru'
    # Check for German characters
    elif any(char in 'äöüßÄÖÜ' for char in text):
        return 'de'
    # Check for Spanish characters
    elif any(char in 'ñáéíóúüÑÁÉÍÓÚÜ' for char in text):
        return 'es'
    # Check for French characters
    elif any(char in 'àâäéèêëïîôùûüÿçÀÂÄÉÈÊËÏÎÔÙÛÜŸÇ' for char in text):
        return 'fr'
    else:
        # Default to English
        return 'en'


def translate_text(text: str, source_lang: str = None, target_lang: str = 'en') -> dict:
    """
    Translate text from source language to target language.
    
    Args:
        text: Text to translate
        source_lang: Source language code (auto-detect if None)
        target_lang: Target language code (default: 'en')
    
    Returns:
        Dictionary with 'translated_text' and 'detected_lang'
    """
    if not text or not text.strip():
        return {'translated_text': text, 'detected_lang': 'en', 'error': 'Empty text'}
    
    try:
        # Auto-detect language if not provided
        if not source_lang:
            source_lang = detect_language(text)
        
        # If source and target are the same, return original
        if source_lang == target_lang:
            return {
                'translated_text': text,
                'detected_lang': source_lang,
                'source_lang': source_lang,
                'target_lang': target_lang
            }
        
        # Load model
        model, tokenizer = load_translation_model(source_lang, target_lang)
        if not model or not tokenizer:
            # Try reverse translation if direct model not available
            reverse_model, reverse_tokenizer = load_translation_model(target_lang, source_lang)
            if reverse_model and reverse_tokenizer:
                logger.warning(f"Using reverse model for {source_lang}->{target_lang}")
                # This is a workaround - we'd need to translate via English
                return {'translated_text': text, 'detected_lang': source_lang, 'error': 'Translation model not available'}
            return {'translated_text': text, 'detected_lang': source_lang, 'error': 'Translation model not available'}
        
        # Tokenize and translate
        # Handle long texts by splitting into chunks if needed
        max_chunk_length = 512  # Maximum tokens per chunk
        chunks = []
        
        # Split text into sentences for better translation quality
        import re
        sentences = re.split(r'([.!?]\s+)', text)
        current_chunk = ""
        
        for i in range(0, len(sentences), 2):
            sentence = sentences[i] + (sentences[i+1] if i+1 < len(sentences) else "")
            test_chunk = current_chunk + sentence
            # Estimate token count (rough approximation: 1 token ≈ 4 characters)
            estimated_tokens = len(test_chunk) // 4
            
            if estimated_tokens > max_chunk_length and current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:
                current_chunk = test_chunk
        
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        # Translate each chunk
        translated_chunks = []
        for chunk in chunks:
            if not chunk.strip():
                continue
                
            # Tokenize chunk
            inputs = tokenizer(chunk, return_tensors="pt", padding=True, truncation=True, max_length=max_chunk_length)
            
            # Generate translation with increased max_length for longer outputs
            translated = model.generate(
                **inputs, 
                max_new_tokens=min(max_chunk_length * 2, 1024),  # Allow longer translations
                num_beams=4,  # Better quality
                early_stopping=True
            )
            translated_chunk = tokenizer.decode(translated[0], skip_special_tokens=True)
            translated_chunks.append(translated_chunk)
        
        # Combine translated chunks
        translated_text = ' '.join(translated_chunks)
        
        logger.info(f"Translated from {source_lang} to {target_lang}: {len(text)} -> {len(translated_text)} chars")
        
        return {
            'translated_text': translated_text,
            'detected_lang': source_lang,
            'source_lang': source_lang,
            'target_lang': target_lang
        }
        
    except Exception as e:
        logger.error(f"Error translating text: {e}")
        return {'translated_text': text, 'detected_lang': source_lang or 'en', 'error': str(e)}


def process_translation_message(ch, method, properties, body):
    """Process translation request from RabbitMQ."""
    try:
        message = json.loads(body)
        request_id = message.get('request_id')
        text = message.get('text', '').strip()
        source_lang = message.get('source_lang')
        target_lang = message.get('target_lang', 'en')
        
        logger.info(f"Processing translation request {request_id}")
        logger.info(f"Text length: {len(text)}, source: {source_lang}, target: {target_lang}")
        
        if not text:
            response = {
                'request_id': request_id,
                'error': 'Empty text provided'
            }
            ch.basic_publish(
                exchange='',
                routing_key=TRANSLATION_RESPONSE_QUEUE,
                body=json.dumps(response),
                properties=pika.BasicProperties(
                    delivery_mode=2,
                    correlation_id=request_id
                )
            )
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return
        
        # Translate text
        result = translate_text(text, source_lang, target_lang)
        
        # Prepare response
        response = {
            'request_id': request_id,
            'translated_text': result.get('translated_text', text),
            'detected_lang': result.get('detected_lang', 'en'),
            'source_lang': result.get('source_lang'),
            'target_lang': result.get('target_lang', target_lang)
        }
        
        if 'error' in result:
            response['error'] = result['error']
        
        # Send response back
        ch.basic_publish(
            exchange='',
            routing_key=TRANSLATION_RESPONSE_QUEUE,
            body=json.dumps(response),
            properties=pika.BasicProperties(
                delivery_mode=2,
                correlation_id=request_id
            )
        )
        
        ch.basic_ack(delivery_tag=method.delivery_tag)
        logger.info(f"Translation completed for request {request_id}")
        
    except Exception as e:
        logger.error(f"Error processing translation message: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def main():
    """Main function to start the translation service."""
    logger.info("Starting Translation Microservice...")
    
    # Pre-load common models (optional, for faster first translation)
    logger.info("Pre-loading common translation models...")
    try:
        load_translation_model('en', 'ru')
        load_translation_model('ru', 'en')
    except Exception as e:
        logger.warning(f"Could not pre-load models: {e}")
    
    # Connect to RabbitMQ
    max_retries = 5
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=RABBITMQ_HOST,
                    port=RABBITMQ_PORT,
                    credentials=credentials
                )
            )
            channel = connection.channel()
            
            # Declare queues
            channel.queue_declare(queue=TRANSLATION_QUEUE, durable=True)
            channel.queue_declare(queue=TRANSLATION_RESPONSE_QUEUE, durable=True)
            
            logger.info(f"Connected to RabbitMQ at {RABBITMQ_HOST}:{RABBITMQ_PORT}")
            logger.info(f"Listening to queue: {TRANSLATION_QUEUE}")
            
            # Set up consumer
            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(
                queue=TRANSLATION_QUEUE,
                on_message_callback=process_translation_message
            )
            
            logger.info("Translation Microservice is ready. Waiting for messages...")
            channel.start_consuming()
            
        except pika.exceptions.AMQPConnectionError as e:
            retry_count += 1
            logger.warning(f"Failed to connect to RabbitMQ (attempt {retry_count}/{max_retries}): {e}")
            if retry_count < max_retries:
                import time
                time.sleep(5)
            else:
                logger.error("Max retries reached. Exiting.")
                sys.exit(1)
        except KeyboardInterrupt:
            logger.info("Stopping Translation Microservice...")
            if 'channel' in locals():
                channel.stop_consuming()
            if 'connection' in locals():
                connection.close()
            break
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            if 'connection' in locals():
                connection.close()
            sys.exit(1)


if __name__ == "__main__":
    main()

