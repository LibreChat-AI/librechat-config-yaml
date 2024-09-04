import json
import requests

def fetch_chat_model_data(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while fetching data: {e}")
        return None

def save_chat_model_ids(data, output_file, include_proxies=True):
    if not data:
        return

    model_proxies = {}
    model_ids_in_order = []

    for model in data.get("data", []):
        if model.get("object") == "model" and model.get("type") == "chat.completions":
            model_id = model["id"]
            model_proxies[model_id] = [model_id]
            model_ids_in_order.append(model_id)

        if include_proxies and model.get("object") == "proxy" and model.get("proxy_to") in model_proxies:
            model_proxies[model.get("proxy_to")].append(model["id"])

    output_list = []
    for model_id in model_ids_in_order:
        output_list.extend(model_proxies[model_id])

    try:
        with open(output_file, "w") as file:
            json.dump(output_list, file, indent=2)
        print(f"Chat model {'and proxy ' if include_proxies else ''}IDs successfully saved to {output_file}")
    except IOError as e:
        print(f"An error occurred while saving the file: {e}")

# Usage
url = "https://api.shuttleai.com/v1/models/verbose"
output_file = "shuttleai.txt"

data = fetch_chat_model_data(url)
if data:
    choice = input("Include proxies? (y/N): ").lower()
    include_proxies = choice == 'y'
    
    if include_proxies:
        output_file = "shuttleai_with_proxies.txt"
    
    save_chat_model_ids(data, output_file, include_proxies)