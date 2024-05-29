import requests
from collections import defaultdict

# This script will fetch and sort all OpenRouter models, and export the results in openrouter.txt

def sort_and_group_ids(ids):
    # Ensure 'openrouter/auto' model is first in the list if present
    first_model = "openrouter/auto"
    if first_model in ids:
        ids.remove(first_model)
    
    # Group IDs by their suffix
    grouped_ids = defaultdict(list)
    sorted_suffixes = [':free', ':nitro', ':beta', ':extended']

    # Sort the ids into categories with suffixes and without suffixes
    for id in ids:
        for suffix in sorted_suffixes:
            if id.endswith(suffix):
                grouped_ids[suffix].append(id)
                break
        else:  # If no suffix was found
            grouped_ids['no_suffix'].append(id)
    
    # Sort each group
    for key in grouped_ids:
        grouped_ids[key].sort()

    # Group 'no_suffix' models by their prefix if count > 2, otherwise put in `others`
    prefix_grouped = defaultdict(list)
    others = []
    
    for id in grouped_ids['no_suffix']:
        prefix = id.split('/')[0]
        prefix_grouped[prefix].append(id)

    for prefix in list(prefix_grouped.keys()):
        if len(prefix_grouped[prefix]) <= 2:
            others.extend(prefix_grouped.pop(prefix))

    prefix_grouped['others'] = sorted(others)  # sort the 'others' group

    # Combine all sorted groups into a single ordered list with titles
    ordered_ids_with_titles = []

    # Add the first model if it was present
    if first_model:
        ordered_ids_with_titles.append(first_model)

    for suffix in sorted_suffixes:
        if grouped_ids[suffix]:
            ordered_ids_with_titles.append(f'---{suffix[1:].upper()}---')
            ordered_ids_with_titles.extend(grouped_ids[suffix])

    for prefix in sorted(prefix_grouped.keys()):
        if prefix != 'others':
            ordered_ids_with_titles.append(f'---{prefix.upper()}---')
            ordered_ids_with_titles.extend(sorted(prefix_grouped[prefix]))

    # Add the 'others' group last
    if 'others' in prefix_grouped and prefix_grouped['others']:
        ordered_ids_with_titles.append('---OTHERS---')
        ordered_ids_with_titles.extend(prefix_grouped['others'])

    return ordered_ids_with_titles

def fetch_and_save_model_ids(url, output_file):
    try:
        # Fetch the data from the URL
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors
        data = response.json()       # Parse the JSON response

        # Extract the "id" fields
        model_ids = [model["id"] for model in data.get("data", []) if "id" in model]

        # Sort and group the IDs
        sorted_ids_with_titles = sort_and_group_ids(model_ids)

        # Format the list of model IDs
        formatted_ids = ',\n'.join(f'"{id}"' for id in sorted_ids_with_titles)

        # Write the formatted list to a file
        with open(output_file, 'w') as file:
            file.write(formatted_ids)
            file.write("\n")  # Ensure the final line ends with a newline

        print(f"Model IDs successfully saved to {output_file}")

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")

# URL for the JSON list
url = "https://openrouter.ai/api/v1/models"
# Output file path
output_file = "openrouter.txt"  # Change the extension as needed, e.g., openrouter.json or openrouter.yaml

# Call the function
fetch_and_save_model_ids(url, output_file)
