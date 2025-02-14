import json
import requests
from bs4 import BeautifulSoup

def fetch_models():
    """Fetch models by scraping the documentation page."""
    url = "https://community.sambanova.ai/t/supported-models/193"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        # Parse HTML and extract model names
        soup = BeautifulSoup(response.text, "html.parser")
        model_names = [code.get_text() for code in soup.find_all("code")]
        
        # Clean and sort the model names
        cleaned_models = sorted(list(set([
            model.strip()
            for model in model_names
            if model.strip()
        ])))
        
        return cleaned_models
        
    except Exception as e:
        print(f"Error fetching models: {str(e)}")
        return None

def main():
    print("Fetching models from SambaNova documentation...")
    models = fetch_models()
    
    if models:
        # Save models to file
        with open("sambanova.txt", "w") as file:
            json.dump(models, file, indent=2)
        print(f"Successfully saved {len(models)} models to sambanova.txt")
    else:
        print("Failed to fetch models.")

if __name__ == "__main__":
    main()
