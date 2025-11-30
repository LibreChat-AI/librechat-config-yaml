import json
import requests
from dotenv import load_dotenv
import os
from pathlib import Path

def get_api_key():
    """Get API key from .env file or environment variables."""
    env_path = Path(__file__).parent / '.env'
    load_dotenv(dotenv_path=env_path)
    key = os.getenv('XAI_API_KEY')
    return key

def fetch_models(api_key):
    """Fetch models from XAI API."""
    url = "https://api.x.ai/v1/models"
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        # Extract and sort model IDs from data array
        model_ids = sorted([
            model['id']
            for model in data['data']
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
    
    print("Fetching models from XAI API...")
    models = fetch_models(api_key)
    
    if models:
        with open("xai.txt", "w") as file:
            json.dump(models, file, indent=2)
        print(f"Successfully saved {len(models)} models to xai.txt")
    else:
        print("Failed to fetch models.")

if __name__ == "__main__":
    main()
