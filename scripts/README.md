# LibreChat YAML Configuration Manager

This tool helps manage and maintain LibreChat YAML configuration files by providing automated updates for model lists and consistent YAML formatting.

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

## Installation

1. Clone this repository:
```bash
git clone https://github.com/LibreChat-AI/librechat-config-yaml.git
cd librechat-config-yaml/scripts
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

3. Copy the environment file and add your API keys:
```bash
cp .env.example .env
```

Edit `.env` and add your API keys for the services you want to use:
```bash
COHERE_API_KEY=your-cohere-key
DEEPSEEK_API_KEY=your-deepseek-key
# ... etc
```

## Usage

Run the main update script:
```bash
python update.py
```

This will:
1. Prompt whether to update YAML formatting (should not be required)
2. Prompt whether to update model lists
3. Create backups before any modifications
4. Process all configuration files:
   - librechat-env-f.yaml
   - librechat-env-l.yaml
   - librechat-up-f.yaml
   - librechat-up-l.yaml
   - librechat-test.yaml

### Individual Scripts

You can also run individual scripts directly:

Convert YAML formatting:
```bash
python convert_yaml_style.py
```

Update model lists:
```bash
python update_models.py
```

## Directory Structure

```
librechat-config-yaml/
├── requirements.txt     # Python dependencies
├── README.md            # This file
├── scripts/             # Helper scripts
│   ├── README.md              # Scripts documentation
│   ├── update.py              # Main script
│   ├── convert_yaml_style.py  # Convert YAML formatting
│   ├── update_models.py       # Update model lists
│   ├── requirements.txt       # Python dependencies
│   ├── .env.example           # Example environment file
│   ├── .env                   # Your API keys (create this)
│   ├── fetch_apipie.py        # Fetch models from APIpie
│   ├── fetch_cohere.py        # Fetch models from Cohere
│   ├── fetch_deepseek.py      # Fetch models from Deepseek
│   ├── fetch_fireworks.py     # Fetch models from Fireworks
│   ├── fetch_github.py        # Fetch models from Github Models
│   ├── fetch_glhf.py          # Fetch models from GLHF.chat
│   ├── fetch_groq.py          # Fetch models from Groq
│   ├── fetch_huggingface.py   # Fetch models from HuggingFace
│   ├── fetch_hyperbolic.py    # Fetch models from Hyperbolic
│   ├── fetch_kluster.py       # Fetch models from Kluster
│   ├── fetch_mistral.py       # Fetch models from Mistral
│   ├── fetch_nanogpt.py       # Fetch models from NanoGPT
│   ├── fetch_nvidia.py        # Fetch models from Nvidia
│   ├── fetch_openrouter.py    # Fetch models from OpenRouter
│   ├── fetch_perplexity.py    # Fetch models from Perplexity
│   ├── fetch_sambanova.py     # Fetch models from SambaNova
│   ├── fetch_together.py      # Fetch models from Together.ai
│   ├── fetch_unify.py         # Fetch models from Unify
│   └── fetch_xai.py           # Fetch models from XAI
└── *.yaml               # LibreChat configuration files
```

## Backup and Safety

- All scripts create `.bak` files before modifying any YAML files
- Logs are written to:
  - `convert_yaml.log` for YAML style conversion
  - `update_models.log` for model updates

## Error Handling

- Failed operations are logged with detailed error messages
- The scripts will continue processing remaining files if one fails
- A summary is displayed after completion showing:
  - Successfully processed files
  - Failed operations
  - Model count updates

## Supported Providers

The tool can update model lists from:
- APIpie
- Cohere
- Deepseek
- Fireworks
- Github Models
- GLHF.chat
- Groq
- HuggingFace
- Hyperbolic
- Kluster
- Mistral
- NanoGPT
- Nvidia
- OpenRouter
- Perplexity
- SambaNova
- Together.ai
- Unify
- XAI

## Contributing

When adding new providers:
1. Create a new fetcher script in the scripts directory
2. Update the provider list in `update_models.py`
3. Add any required API keys to `.env.example`