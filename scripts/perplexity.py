import json
import requests
from bs4 import BeautifulSoup

def fetch_models():
    """Fetch models by scraping the documentation page."""
    url = "https://docs.perplexity.ai/guides/model-cards"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Find all tables
        tables = soup.find_all('table')
        if not tables:
            print("No tables found in documentation")
            return None
            
        # Get the first table (current models)
        current_models_table = tables[0]
        
        # Extract model names from first column
        models = []
        for row in current_models_table.find_all('tr')[1:]:  # Skip header row
            cols = row.find_all('td')
            if cols:
                model_name = cols[0].text.strip()
                if model_name:
                    models.append(model_name)
        
        return sorted(models)
        
    except Exception as e:
        print(f"Error fetching models: {str(e)}")
        return None

def main():
    print("Fetching models from Perplexity documentation...")
    models = fetch_models()
    
    if models:
        # Save models to file
        with open("perplexity.txt", "w") as file:
            json.dump(models, file, indent=2)
        print(f"Successfully saved {len(models)} models to perplexity.txt")
    else:
        print("Failed to fetch models.")

if __name__ == "__main__":
    main()
