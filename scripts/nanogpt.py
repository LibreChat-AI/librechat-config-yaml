import json
import requests

def fetch_models():
    """Fetch models from NanoGPT's public API."""
    url = "https://nano-gpt.com/api/models"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        data = response.json()
        # Extract models from the nested structure
        if 'models' in data and 'text' in data['models']:
            # Get all model entries from the text section
            text_models = data['models']['text']
            # Extract and sort model IDs
            model_ids = sorted([
                model_info['model']
                for model_info in text_models.values()
                if isinstance(model_info, dict) and 'model' in model_info
            ])
            return model_ids
            
    except Exception as e:
        print(f"Error fetching models: {str(e)}")
        return None

def main():
    print("Fetching models from NanoGPT API...")
    models = fetch_models()
    
    if models:
        with open("nanogpt.txt", "w") as file:
            json.dump(models, file, indent=2)
        print(f"Successfully saved {len(models)} models to nanogpt.txt")
    else:
        print("Failed to fetch models.")

if __name__ == "__main__":
    main()
