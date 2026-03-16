import json
import logging
import requests
from bs4 import BeautifulSoup

from log_config import setup_logging

logger = logging.getLogger(__name__)

def fetch_models():
    """Fetch models by scraping the documentation page."""
    url = "https://docs.perplexity.ai/guides/model-cards"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Find all tables
        tables = soup.find_all('table')
        if not tables:
            logger.warning("No tables found in documentation")
            return None
            
        # Get the first table (current models)
        current_models_table = tables[0]
        
        # Extract model names from first column
        models = []
        for row in current_models_table.find_all('tr')[1:]:  # Skip header row
            cols = row.find_all('td')
            if cols:
                model_name = cols[0].text.strip()
                if model_name:
                    models.append(model_name)
        
        return sorted(models)
        
    except Exception as e:
        logger.error("Error fetching models: %s", e)
        return None

def main():
    logger.info("Fetching models from %s API", "Perplexity")
    models = fetch_models()

    if models:
        # Save models to file
        with open("perplexity.txt", "w") as file:
            json.dump(models, file, indent=2)
        logger.info("Successfully saved %d models to %s", len(models), "perplexity.txt")
    else:
        logger.error("Failed to fetch models")

if __name__ == "__main__":
    setup_logging()
    main()
