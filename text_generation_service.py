"""
Text Generation Microservice using GPT2 model.
Listens to RabbitMQ queue and generates text based on user input.
"""
import os
import sys
import json
import logging
import pika
from transformers import GPT2LMHeadModel, GPT2Tokenizer
import torch

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
TEXT_GENERATION_QUEUE = 'text_generation_queue'
TEXT_GENERATION_RESPONSE_QUEUE = 'text_generation_response_queue'

# GPT2 Model
_model = None
_tokenizer = None


def load_gpt2_model():
    """Load GPT2 model once."""
    global _model, _tokenizer
    if _model is None or _tokenizer is None:
        logger.info("Loading GPT2 model...")
        try:
            model_name = "gpt2"  # Using base GPT2 model
            _tokenizer = GPT2Tokenizer.from_pretrained(model_name)
            _model = GPT2LMHeadModel.from_pretrained(model_name)
            _model.eval()  # Set to evaluation mode
            
            # Set pad_token to eos_token if not set
            if _tokenizer.pad_token is None:
                _tokenizer.pad_token = _tokenizer.eos_token
            
            logger.info("GPT2 model loaded successfully")
        except Exception as e:
            logger.error(f"Error loading GPT2 model: {e}")
            raise
    return _model, _tokenizer


def generate_text(prompt: str, max_new_tokens: int = 60, temperature: float = 0.75) -> str:
    """
    Generate text based on prompt using GPT2.
    
    Args:
        prompt: Input text or tags to generate from
        max_new_tokens: Maximum number of tokens to generate
        temperature: Sampling temperature (higher = more creative)
    
    Returns:
        Generated text
    """
    if not prompt or not prompt.strip():
        raise ValueError("Prompt cannot be empty")
    
    try:
        model, tokenizer = load_gpt2_model()
        
        # Tokenize input
        inputs = tokenizer.encode(prompt, return_tensors='pt', max_length=512, truncation=True)
        
        if inputs.size(1) == 0:
            raise ValueError("Failed to tokenize prompt")
        
        # Generate text
        with torch.no_grad():
            outputs = model.generate(
                inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                do_sample=True,
                top_p=0.9,
                repetition_penalty=1.1,
                pad_token_id=tokenizer.eos_token_id
            )
        
        # Decode generated text
        generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Remove the original prompt from the generated text
        if generated_text.startswith(prompt):
            generated_text = generated_text[len(prompt):].strip()
        
        # Clean up the text (remove extra whitespace, fix punctuation)
        generated_text = ' '.join(generated_text.split())
        
        # Limit to reasonable length (approximately 3-5 sentences)
        sentences = generated_text.split('. ')
        if len(sentences) > 5:
            generated_text = '. '.join(sentences[:5])
            if not generated_text.endswith('.'):
                generated_text += '.'
        
        logger.info(f"Generated text length: {len(generated_text)} characters")
        return generated_text
        
    except Exception as e:
        logger.error(f"Error generating text: {e}")
        raise


def process_text_generation_message(ch, method, properties, body):
    """Process text generation request from RabbitMQ."""
    try:
        message = json.loads(body)
        request_id = message.get('request_id')
        prompt_text = message.get('prompt_text', '').strip()
        tags = message.get('tags', '').strip()
        max_new_tokens = message.get('max_new_tokens', 60)
        temperature = message.get('temperature', 0.75)
        
        logger.info(f"Processing text generation request {request_id}")
        logger.info(f"Prompt: {prompt_text[:50]}...")
        logger.info(f"Tags: {tags}")
        
        # Build prompt based on what user provided
        if prompt_text and tags:
            # Both text and tags: improve text and add tags at the end
            prompt = f"{prompt_text} {tags}"
            final_prompt = f"Continue and improve this social media post, make it more engaging and detailed: {prompt_text}"
        elif prompt_text:
            # Only text: improve/continue it
            final_prompt = f"Continue and improve this social media post, make it more engaging and detailed: {prompt_text}"
        elif tags:
            # Only tags: generate post about tags
            final_prompt = f"Write an interesting social media post about {tags}. Make it engaging and personal."
        else:
            # Empty: return error
            response = {
                'request_id': request_id,
                'error': 'Please enter text or tags to generate a post'
            }
            ch.basic_publish(
                exchange='',
                routing_key=TEXT_GENERATION_RESPONSE_QUEUE,
                body=json.dumps(response),
                properties=pika.BasicProperties(
                    delivery_mode=2,
                    correlation_id=request_id
                )
            )
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return
        
        # Generate text
        generated_text = generate_text(final_prompt, max_new_tokens, temperature)
        
        # Combine with original text and tags
        if prompt_text:
            # If user had text, append generated text
            final_text = f"{prompt_text} {generated_text}".strip()
        else:
            # If only tags, use generated text
            final_text = generated_text
        
        # Add tags at the end if they exist
        if tags:
            final_text = f"{final_text} {tags}".strip()
        
        # Prepare response
        response = {
            'request_id': request_id,
            'generated_text': final_text
        }
        
        # Send response back
        ch.basic_publish(
            exchange='',
            routing_key=TEXT_GENERATION_RESPONSE_QUEUE,
            body=json.dumps(response),
            properties=pika.BasicProperties(
                delivery_mode=2,
                correlation_id=request_id
            )
        )
        
        ch.basic_ack(delivery_tag=method.delivery_tag)
        logger.info(f"Text generation completed for request {request_id}")
        
    except Exception as e:
        logger.error(f"Error processing text generation message: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def main():
    """Main function to start the text generation service."""
    logger.info("Starting Text Generation Microservice...")
    
    # Load model
    try:
        load_gpt2_model()
    except Exception as e:
        logger.error(f"Failed to load GPT2 model: {e}")
        sys.exit(1)
    
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
            channel.queue_declare(queue=TEXT_GENERATION_QUEUE, durable=True)
            channel.queue_declare(queue=TEXT_GENERATION_RESPONSE_QUEUE, durable=True)
            
            logger.info(f"Connected to RabbitMQ at {RABBITMQ_HOST}:{RABBITMQ_PORT}")
            logger.info(f"Listening to queue: {TEXT_GENERATION_QUEUE}")
            
            # Set up consumer
            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(
                queue=TEXT_GENERATION_QUEUE,
                on_message_callback=process_text_generation_message
            )
            
            logger.info("Text Generation Microservice is ready. Waiting for messages...")
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
            logger.info("Stopping Text Generation Microservice...")
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
