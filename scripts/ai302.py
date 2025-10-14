import json
import requests
from dotenv import load_dotenv
import os
from pathlib import Path

def get_api_key():
    """Get API key from .env file or environment variables."""
    env_path = Path(__file__).parent / '.env'
    load_dotenv(dotenv_path=env_path)
    key = os.getenv('AI302_API_KEY')
    return key

def fetch_models(api_key):
    """Fetch models from 302AI API."""
    url = "https://api.302.ai/v1/models?llm=1"
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        if 'data' in data:
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
    api_key = get_api_key()
    
    if not api_key:
        print("No API key provided. Skipping model fetch.")
        return
    
    print("Fetching models from 302AI API...")
    models = fetch_models(api_key)
    
    if models:
        with open("ai302.txt", "w") as file:
            json.dump(models, file, indent=2)
        print(f"Successfully saved {len(models)} models to ai302.txt")
    else:
        print("Failed to fetch models.")

if __name__ == "__main__":
    main()