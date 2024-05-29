import json
import requests

# Fetch and alphabetize models from APIpie and output the results in apipie.txt

def fetch_and_order_models():
    # API endpoint
    url = "https://apipie.ai/models"

    # headers as per request example
    headers = {"Accept": "application/json"}

    # request parameters for "vision" models
    params_vision = {"type": "vision"}

    # request parameters for "llm" models
    params_llm = {"type": "llm"}

    # make request for "vision" models
    response_vision = requests.get(url, headers=headers, params=params_vision)

    # make request for "llm" models
    response_llm = requests.get(url, headers=headers, params=params_llm)

    # parse JSON responses
    data_vision = response_vision.json()
    data_llm = response_llm.json()

    # combine the results
    data = data_vision + data_llm

    # extract an ordered list of unique model IDs
    model_ids = sorted(set([model["id"] for model in data]))

    # write result to a text file
    with open("apipie.txt", "w") as file:
        json.dump(model_ids, file, indent=2)

# execute the function
if __name__ == "__main__":
    fetch_and_order_models()
