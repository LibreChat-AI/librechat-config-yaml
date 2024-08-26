import requests

def fetch_endpoints(api_key):
    url = 'https://api.unify.ai/v0/endpoints'
    headers = {
        'Authorization': f'Bearer {api_key}',
        'accept': 'application/json',
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        try:
            return response.json()  # Parse JSON response
        except ValueError:
            print("Error: Response content is not valid JSON.")
            return None
    else:
        print(f"Failed to fetch endpoints. Status code: {response.status_code}")
        return None

def format_endpoints(endpoints):
    # Ensure endpoints is a list
    if not isinstance(endpoints, list):
        print("Error: Endpoints data is not in the expected format.")
        return None

    # Organize by provider
    provider_dict = {}
    for endpoint in endpoints:
        model, provider = endpoint.split('@')
        if provider not in provider_dict:
            provider_dict[provider] = []
        provider_dict[provider].append(model)
    
    # Create a formatted result with trailing commas and quotes
    formatted_result = []
    for provider, models in provider_dict.items():
        for model in models:
            formatted_result.append(f'"{model}@{provider}",')
    
    return '\n'.join(formatted_result)

def save_formatted_endpoints(formatted_endpoints, file_path):
    with open(file_path, 'w') as file:
        file.write(formatted_endpoints)

def main():
    api_key = input("Please enter your API key: ")
    
    endpoints_data = fetch_endpoints(api_key)
    
    if endpoints_data:
        formatted_endpoints = format_endpoints(endpoints_data)
        
        if formatted_endpoints:
            save_formatted_endpoints(formatted_endpoints, 'unify.txt')
            print("Formatted endpoints saved to unify.txt")
        else:
            print("Failed to format endpoints.")
    else:
        print("No data retrieved.")

if __name__ == "__main__":
    main()
