import json
import requests

def fetch_models():
    """Fetch models from GitHub's Azure inference API."""
    url = "https://models.inference.ai.azure.com/models"
    headers = {
        "accept": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers)
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
        print(f"Error fetching models: {str(e)}")
        return None

def main():
    print("Fetching models from GitHub...")
    models = fetch_models()
    
    if models:
        with open("github.txt", "w") as file:
            json.dump(models, file, indent=2)
        print(f"Successfully saved {len(models)} models to github.txt")
    else:
        print("Failed to fetch models.")

if __name__ == "__main__":
    main()
