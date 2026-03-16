import json
import logging
import requests
from bs4 import BeautifulSoup

from log_config import setup_logging

logger = logging.getLogger(__name__)

def fetch_models():
    """Fetch models by scraping the documentation page."""
    url = "https://community.sambanova.ai/t/supported-models/193"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        # Parse HTML and extract model names
        soup = BeautifulSoup(response.text, "html.parser")
        model_names = [code.get_text() for code in soup.find_all("code")]
        
        # Clean and sort the model names
        cleaned_models = sorted(list(set([
            model.strip()
            for model in model_names
            if model.strip()
        ])))
        
        return cleaned_models
        
    except Exception as e:
        logger.error("Error fetching models: %s", e)
        return None

def main():
    logger.info("Fetching models from %s API", "SambaNova")
    models = fetch_models()

    if models:
        # Save models to file
        with open("sambanova.txt", "w") as file:
            json.dump(models, file, indent=2)
        logger.info("Successfully saved %d models to %s", len(models), "sambanova.txt")
    else:
        logger.error("Failed to fetch models")

if __name__ == "__main__":
    setup_logging()
    main()
