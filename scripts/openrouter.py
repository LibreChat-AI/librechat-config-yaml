from pathlib import Path
from typing import Iterable

import requests
import json
from collections import defaultdict

def sort_and_group_ids(ids, stealth_models=None):
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

            # Add stealth models right after FREE category
            if suffix == ':free' and stealth_models and len(stealth_models) > 0:
                models_list.append('---STEALTH---')
                models_list.extend(sorted(stealth_models))

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

def get_stealth_models():
    """Prompt the user for stealth models if they want to add them."""
    add_stealth = input("Do you want to add or update stealth models? (y/n): ").lower().strip()

    if add_stealth == 'y' or add_stealth == 'yes':
        saved_models = []
        try:
            with open("openrouter.txt", 'r') as file:
                all_models = json.load(file)

                # Find STEALTH section and extract models
                stealth_section = False
                for item in all_models:
                    if item == "---STEALTH---":
                        stealth_section = True
                        continue
                    elif stealth_section and item.startswith("---"):
                        break
                    elif stealth_section:
                        saved_models.append(item)

                if saved_models:
                    print("Currently saved stealth models:")
                    print(", ".join(saved_models))
        except (FileNotFoundError, json.JSONDecodeError):
            pass

        stealth_input = input("Enter comma-separated list of stealth model IDs: ").strip()
        if stealth_input:
            # Split by commas and clean up whitespace
            return [model.strip() for model in stealth_input.split(',')]

    return []

def fetch_and_save_model_ids(url, output_file):
    try:
        # Get stealth models first
        stealth_models = get_stealth_models()

        # Fetch the data from the URL
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        # Extract the "id" fields
        model_ids = [model["id"] for model in data.get("data", []) if "id" in model]

        # Sort and group the IDs
        sorted_models = sort_and_group_ids(model_ids, stealth_models)

        # Save as JSON array
        with open(output_file, 'w') as file:
            json.dump(sorted_models, file, indent=2)
            dump_endpoints(endpoints=sorted_models)

        print(f"Model IDs successfully saved to {output_file}")

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")


def dump_endpoints(endpoints: Iterable[str], path: Path | str = Path("endpoints.yaml")) -> Path:
    """
    Dump a list of strings to a YAML file (as a top-level sequence).
    No external libraries required.

    - Each item is double-quoted and safely escaped.
    - Writes UTF-8 with a trailing newline.
    - Returns the path written to.
    """
    p = Path(path)

    def yaml_quote(s: str) -> str:
        # Double-quoted YAML scalar with escaped specials.
        out: list[str] = []
        for ch in s:
            code = ord(ch)
            if ch == "\\":
                out.append("\\\\")
            elif ch == '"':
                out.append('\\"')
            elif ch == "\n":
                out.append("\\n")
            elif ch == "\t":
                out.append("\\t")
            elif ch == "\r":
                out.append("\\r")
            elif code < 0x20:
                # Other ASCII control chars -> \xNN
                out.append(f"\\x{code:02x}")
            else:
                out.append(ch)
        entry = "".join(out)
        if entry.startswith("--"):
            # Models don't have quotes, but sections do.
            entry = f"'{entry}'"
        return entry

    # Build YAML content
    lines = ["---"]
    for item in endpoints:
        lines.append(f"- {yaml_quote(str(item))}")
    lines.append("")  # ensure trailing newline

    p.write_text("\n".join(lines), encoding="utf-8")
    return p

def main():
    # URL for the JSON list
    url = "https://openrouter.ai/api/v1/models"
    # Output file path
    output_file = "openrouter.txt"

    fetch_and_save_model_ids(url, output_file)

if __name__ == "__main__":
    main()
