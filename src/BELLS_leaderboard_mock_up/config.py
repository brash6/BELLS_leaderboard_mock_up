import os
from pathlib import Path
from dotenv import load_dotenv

def load_config():
    """Load configuration from environment variables"""
    # Try to load from .env file if it exists
    env_path = Path(__file__).parent.parent.parent / '.env'
    load_dotenv(env_path)
    
    # Get OpenAI API key from environment variable
    openai_api_key = os.getenv('OPENAI_API_KEY')
    
    if not openai_api_key:
        raise ValueError(
            "OpenAI API key not found. Please set the OPENAI_API_KEY environment variable "
            "either in your environment or in a .env file."
        )
    
    return {
        'openai_api_key': openai_api_key
    } 