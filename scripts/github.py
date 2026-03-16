import json
import logging
import httpx

from log_config import setup_logging

logger = logging.getLogger(__name__)

def fetch_models():
    """Fetch models from GitHub's Azure inference API."""
    url = "https://models.inference.ai.azure.com/models"
    headers = {
        "accept": "application/json"
    }
    
    try:
        response = httpx.get(url, headers=headers, timeout=30.0, follow_redirects=True)
        response.raise_for_status()
        
        data = response.json()
        # Extract and sort model names instead of IDs
        model_names = sorted([
            model['name']
            for model in data
            if 'name' in model
        ])
        return model_names
            
    except Exception as e:
        logger.error("Error fetching models: %s", e)
        return None

def main():
    logger.info("Fetching models from %s API", "GitHub")
    models = fetch_models()

    if models:
        with open("github.txt", "w") as file:
            json.dump(models, file, indent=2)
        logger.info("Successfully saved %d models to %s", len(models), "github.txt")
    else:
        logger.error("Failed to fetch models")

if __name__ == "__main__":
    setup_logging()
    main()
