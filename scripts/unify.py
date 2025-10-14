import json
import requests
from dotenv import load_dotenv
import os
from pathlib import Path

def get_api_key():
    """Get API key from .env file or environment variables."""
    env_path = Path(__file__).parent / '.env'
    load_dotenv(dotenv_path=env_path)
    key = os.getenv('UNIFY_API_KEY')
    return key

def fetch_models(api_key):
    """Fetch models from Unify API."""
    url = 'https://api.unify.ai/v0/endpoints'
    headers = {
        'Authorization': f'Bearer {api_key}',
        'accept': 'application/json',
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        if isinstance(data, list):
            # Extract and sort model names with providers
            model_ids = sorted([
                f"{model.split('@')[0]}@{model.split('@')[1]}"
                for model in data
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
    
    print("Fetching models from Unify API...")
    models = fetch_models(api_key)
    
    if models:
        with open("unify.txt", "w") as file:
            json.dump(models, file, indent=2)
        print(f"Successfully saved {len(models)} models to unify.txt")
    else:
        print("Failed to fetch models.")

if __name__ == "__main__":
    main()
