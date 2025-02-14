import requests
import json
from collections import defaultdict

def sort_and_group_ids(ids):
    """Sort and group model IDs, including category headers."""
    first_model = "openrouter/auto"
    models_list = []
    
    if first_model in ids:
        ids.remove(first_model)
        models_list.append(first_model)
    
    # Group IDs by their suffix
    grouped_ids = defaultdict(list)
    sorted_suffixes = [':free', ':nitro', ':beta', ':extended']

    # Sort into categories with suffixes and without suffixes
    for id in ids:
        for suffix in sorted_suffixes:
            if id.endswith(suffix):
                grouped_ids[suffix].append(id)
                break
        else:
            grouped_ids['no_suffix'].append(id)
    
    # Sort each group
    for key in grouped_ids:
        grouped_ids[key].sort()

    # Group 'no_suffix' models by their prefix
    prefix_grouped = defaultdict(list)
    others = []
    
    for id in grouped_ids['no_suffix']:
        prefix = id.split('/')[0]
        prefix_grouped[prefix].append(id)

    # Move small groups to others
    for prefix in list(prefix_grouped.keys()):
        if len(prefix_grouped[prefix]) <= 2:
            others.extend(prefix_grouped.pop(prefix))

    prefix_grouped['others'] = sorted(others)

    # Add sorted groups to the final list with headers
    for suffix in sorted_suffixes:
        if grouped_ids[suffix]:
            models_list.append(f'---{suffix[1:].upper()}---')
            models_list.extend(grouped_ids[suffix])

    # Add prefix groups with headers
    for prefix in sorted(prefix_grouped.keys()):
        if prefix != 'others':
            models_list.append(f'---{prefix.upper()}---')
            models_list.extend(sorted(prefix_grouped[prefix]))

    # Add the others group last
    if prefix_grouped['others']:
        models_list.append('---OTHERS---')
        models_list.extend(prefix_grouped['others'])
    
    return models_list

def fetch_and_save_model_ids(url, output_file):
    try:
        # Fetch the data from the URL
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        # Extract the "id" fields
        model_ids = [model["id"] for model in data.get("data", []) if "id" in model]

        # Sort and group the IDs
        sorted_models = sort_and_group_ids(model_ids)

        # Save as JSON array
        with open(output_file, 'w') as file:
            json.dump(sorted_models, file, indent=2)

        print(f"Model IDs successfully saved to {output_file}")

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")

def main():
    # URL for the JSON list
    url = "https://openrouter.ai/api/v1/models"
    # Output file path
    output_file = "openrouter.txt"
    
    fetch_and_save_model_ids(url, output_file)

if __name__ == "__main__":
    main()
