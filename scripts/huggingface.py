import json
import logging
import requests
from time import sleep

from log_config import setup_logging

logger = logging.getLogger(__name__)

def fetch_models(page=1, limit=100):
    """Fetch text generation models from Hugging Face API."""
    url = "https://huggingface.co/api/models"
    params = {
        "filter": "conversational",
        "sort": "likes",  # Changed from "trending" to "likes"
        "direction": "-1",
        "limit": limit,
        "full": "true",
        "page": page
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error("Error fetching page %d: %s", page, e)
        return None

def main():
    logger.info("Fetching models from %s API", "Hugging Face")
    all_models = []
    page = 1
    max_pages = 5  # Add page limit

    while page <= max_pages:  # Change condition to use max_pages
        logger.info("Fetching page %d of %d", page, max_pages)
        models = fetch_models(page=page)
        
        if not models:
            break
            
        # Extract model IDs and filter out non-text models
        model_ids = [
            model['modelId'] 
            for model in models 
            if model.get('pipeline_tag') == 'text-generation'
        ]
        
        if not model_ids:
            break
            
        all_models.extend(model_ids)
        logger.info("Found %d models on page %d", len(model_ids), page)
        
        # Check if we've reached the end of results
        if len(models) < 100:
            break
            
        page += 1
        sleep(1)  # Be nice to the API
    
    if all_models:
        # Remove duplicates and sort
        unique_models = sorted(list(set(all_models)))
        
        with open("huggingface.txt", "w") as file:
            json.dump(unique_models, file, indent=2)
        logger.info("Successfully saved %d models to %s", len(unique_models), "huggingface.txt")
    else:
        logger.error("Failed to fetch models")

if __name__ == "__main__":
    setup_logging()
    main()
