import json
import logging
import requests

from log_config import setup_logging

logger = logging.getLogger(__name__)

def fetch_models():
    """Fetch models from NVIDIA's public API."""
    url = "https://integrate.api.nvidia.com/v1/models"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        data = response.json()
        if 'data' in data and isinstance(data['data'], list):
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
    logger.info("Fetching models from %s API", "NVIDIA")
    models = fetch_models()

    if models:
        with open("nvidia.txt", "w") as file:
            json.dump(models, file, indent=2)
        logger.info("Successfully saved %d models to %s", len(models), "nvidia.txt")
    else:
        logger.error("Failed to fetch models")

if __name__ == "__main__":
    setup_logging()
    main()
