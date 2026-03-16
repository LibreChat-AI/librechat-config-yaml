import json
import logging
import requests

from log_config import setup_logging

logger = logging.getLogger(__name__)

def sort_models(ids):
    """Simple sort with free models first."""
    # Separate free models and others
    free_models = sorted([id for id in ids if str(id).startswith('free/')])
    other_models = sorted([id for id in ids if not str(id).startswith('free/')])
    
    # Combine with a header for free models if they exist
    result = []
    if free_models:
        result.append('---FREE---')
        result.extend(free_models)
    result.extend(other_models)
    
    return result

def fetch_and_order_models():
    # API endpoint
    url = "https://apipie.ai/models"
    headers = {"Accept": "application/json"}
    
    try:
        # Make requests for different model types
        params_types = {
            "free": {"type": "free"},
            "vision": {"type": "vision"},
            "llm": {"type": "llm"}
        }
        
        all_models = set()
        
        for param_type in params_types.values():
            try:
                response = requests.get(url, headers=headers, params=param_type)
                response.raise_for_status()
                data = response.json()
                
                if isinstance(data, list):
                    for model in data:
                        if isinstance(model, dict) and 'id' in model:
                            model_id = str(model['id'])
                            all_models.add(model_id)
            except requests.exceptions.RequestException as e:
                logger.warning("Error fetching %s models: %s", param_type, e)
                continue
        
        # Sort the models
        sorted_models = sort_models(list(all_models))
        
        # Write result to a text file
        with open("apipie.txt", "w", encoding='utf-8') as file:
            json.dump(sorted_models, file, indent=2)
            
        logger.info("Successfully saved %d models to apipie.txt", len(sorted_models))

    except Exception as e:
        logger.error("Unexpected error: %s", e)

def main():
    fetch_and_order_models()

if __name__ == "__main__":
    setup_logging()
    main()
