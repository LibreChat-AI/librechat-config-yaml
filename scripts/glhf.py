import json
import logging
import requests
from dotenv import load_dotenv
import os
from pathlib import Path

from log_config import setup_logging

logger = logging.getLogger(__name__)

def get_api_key():
    """Get API key from .env file or environment variables."""
    env_path = Path(__file__).parent / '.env'
    load_dotenv(dotenv_path=env_path)
    key = os.getenv('GLHF_API_KEY')
    return key

def fetch_models(api_key):
    """Fetch models from GLHF API."""
    url = "https://glhf.chat/api/openai/v1/models"
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        if 'data' in data:
            # Extract and sort model IDs
            model_ids = sorted([
                model['id']
                for model in data['data']
                if 'id' in model
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

    logger.info("Fetching models from %s API", "GLHF")
    models = fetch_models(api_key)

    if models:
        with open("glhf.txt", "w") as file:
            json.dump(models, file, indent=2)
        logger.info("Successfully saved %d models to %s", len(models), "glhf.txt")
    else:
        logger.error("Failed to fetch models")

if __name__ == "__main__":
    setup_logging()
    main()
