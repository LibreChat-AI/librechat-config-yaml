import json
import requests

def get_api_key():
    return input("Please enter your API key: ")

# API endpoint
url = "https://api.together.xyz/v1/models"

def main():
    # Get API key from user input
    api_key = get_api_key()

    # headers
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    # make request
    response = requests.get(url, headers=headers)

    # Print status code and content for debugging
    print(f"Status Code: {response.status_code}")
    print(f"Response Content: {response.text}")

    # Check if the request was successful
    if response.status_code == 200:
        try:
            data = response.json()
        except requests.exceptions.JSONDecodeError:
            print("Failed to decode JSON. Response content:", response.text)
        else:
            # extract an ordered list of unique model IDs
            model_ids = sorted(
                [
                    model['id']
                    for model in data
                    if model['type'] == 'chat'
                ]
            )

            # write result to a text file
            with open("models_togetherai.json", "w") as file:
                json.dump(model_ids, file, indent=2)
            
            print("Model IDs have been written to models_togetherai.json")
    else:
        print(f"Request failed with status code: {response.status_code}")

if __name__ == "__main__":
    main()
