import json
import logging
import requests

from log_config import setup_logging

logger = logging.getLogger(__name__)

def fetch_models():
    """Fetch models from NanoGPT's public API."""
    url = "https://nano-gpt.com/api/models"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        data = response.json()
        # Extract models from the nested structure
        if 'models' in data and 'text' in data['models']:
            # Get all model entries from the text section
            text_models = data['models']['text']
            # Extract and sort model IDs
            model_ids = sorted([
                model_info['model']
                for model_info in text_models.values()
                if isinstance(model_info, dict) and 'model' in model_info
            ])
            return model_ids
            
    except Exception as e:
        logger.error("Error fetching models: %s", e)
        return None

def main():
    logger.info("Fetching models from %s API", "NanoGPT")
    models = fetch_models()

    if models:
        with open("nanogpt.txt", "w") as file:
            json.dump(models, file, indent=2)
        logger.info("Successfully saved %d models to %s", len(models), "nanogpt.txt")
    else:
        logger.error("Failed to fetch models")

if __name__ == "__main__":
    setup_logging()
    main()
