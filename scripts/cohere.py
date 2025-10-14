import json
import requests
from dotenv import load_dotenv
import os
from pathlib import Path

def get_api_key():
    """Get API key from .env file or environment variables."""
    env_path = Path(__file__).parent / '.env'
    load_dotenv(dotenv_path=env_path)
    key = os.getenv('COHERE_API_KEY')
    return key

def fetch_models(api_key):
    """Fetch models from Cohere API."""
    url = "https://api.cohere.com/v1/models"
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        if 'models' in data:
            # Extract and sort model names, filtering for chat-capable models
            model_ids = sorted([
                model['name']
                for model in data['models']
                if 'chat' in model.get('endpoints', [])
            ])
            return model_ids
            
    except Exception as e:
        print(f"Error fetching models: {str(e)}")
        return None

def main():
    api_key = get_api_key()
    
    if not api_key:
        print("No API key provided. Skipping model fetch.")
        return
    
    print("Fetching models from Cohere API...")
    models = fetch_models(api_key)
    
    if models:
        with open("cohere.txt", "w") as file:
            json.dump(models, file, indent=2)
        print(f"Successfully saved {len(models)} models to cohere.txt")
    else:
        print("Failed to fetch models.")

if __name__ == "__main__":
    main()
