import json
import requests

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
        print(f"Error fetching models: {str(e)}")
        return None

def main():
    print("Fetching models from NVIDIA API...")
    models = fetch_models()
    
    if models:
        with open("nvidia.txt", "w") as file:
            json.dump(models, file, indent=2)
        print(f"Successfully saved {len(models)} models to nvidia.txt")
    else:
        print("Failed to fetch models.")

if __name__ == "__main__":
    main()
