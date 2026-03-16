import json
import logging
import httpx
from dotenv import load_dotenv
import os
from pathlib import Path

from log_config import setup_logging

logger = logging.getLogger(__name__)

def get_api_key():
    """Get API key from .env file or environment variables."""
    env_path = Path(__file__).parent / '.env'
    load_dotenv(dotenv_path=env_path)
    key = os.getenv('GROQ_API_KEY')
    return key

def fetch_models(api_key):
    """Fetch models from Groq API."""
    url = "https://api.groq.com/openai/v1/models"
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    try:
        response = httpx.get(url, headers=headers, timeout=30.0, follow_redirects=True)
        response.raise_for_status()
        
        data = response.json()
        if 'data' in data:
            # Extract and sort model IDs, filtering out whisper models
            model_ids = sorted([
                model['id']
                for model in data['data']
                if 'id' in model and 'whisper' not in model['id'].lower()
            ])
            return model_ids
            
    except Exception as e:
        logger.error("Error fetching models: %s", e)
        return None

def main():
    api_key = get_api_key()
    
    if not api_key:
        logger.warning("No API key provided, skipping model fetch")
        return

    logger.info("Fetching models from %s API", "Groq")
    models = fetch_models(api_key)

    if models:
        with open("groq.txt", "w") as file:
            json.dump(models, file, indent=2)
        logger.info("Successfully saved %d models to %s", len(models), "groq.txt")
    else:
        logger.error("Failed to fetch models")

if __name__ == "__main__":
    setup_logging()
    main()
