import json
import requests

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
                print(f"Warning: Error fetching {param_type} models: {e}")
                continue
        
        # Sort the models
        sorted_models = sort_models(list(all_models))
        
        # Write result to a text file
        with open("apipie.txt", "w", encoding='utf-8') as file:
            json.dump(sorted_models, file, indent=2)
            
        print(f"Successfully saved {len(sorted_models)} models to apipie.txt")

    except Exception as e:
        print(f"Unexpected error: {e}")

def main():
    fetch_and_order_models()

if __name__ == "__main__":
    main()
