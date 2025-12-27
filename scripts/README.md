# LibreChat YAML Configuration Manager

Automated tool for maintaining LibreChat YAML configurations with up-to-date model lists from 20+ AI providers.

## Quick Start

**Prerequisites:** Python 3.8+ and pip

```bash
# Create a virtual environment
python -m venv privacy-venv
source privacy-venv/Scripts/activate  # On Windows use: privacy-venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# For local use, configure API keys
cp .env.example .env
# Edit .env with your API keys
```

## Usage

### Interactive Mode (Manual Updates)

Run the main update script:
```bash
python update.py
```

This will:
1. Prompt whether to update YAML formatting (should not be required)
2. Prompt whether to update model lists
3. Create backups before any modifications
4. Process configuration files

### Automated Mode (No Prompts)

For automated/scheduled runs without user interaction:

```bash
# Update all YAML files
python update.py --automated
```

Or using environment variables:
```bash
AUTOMATED_MODE=true python update.py
```

### Dedicated Automated Script

For GitHub Actions and other CI/CD pipelines:

```bash
# Runs automated update with YAML validation
cd scripts
python automated_update.py
```

This script:
- Fetches latest models from all providers
- Updates all YAML files
- Validates YAML syntax
- Returns appropriate exit codes:
  - `0`: Success
  - `1`: Update failed
  - `2`: YAML validation failed

### Individual Scripts

You can also run individual scripts directly:

Convert YAML formatting:
```bash
python convert_yaml_style.py
```

Update model lists:
```bash
# Interactive mode
python update_models.py
```

## GitHub Actions (Automated Weekly Updates)

This repository includes automated weekly model updates via GitHub Actions.

### Setup Instructions

1. **Add Repository Secrets**

   Go to your repository Settings → Secrets and variables → Actions, and add the following secrets:

   ```
   AI302_API_KEY
   APIPIE_API_KEY
   COHERE_API_KEY
   DEEPSEEK_API_KEY
   FIREWORKS_API_KEY
   GLHF_API_KEY
   GROQ_API_KEY
   HUGGINGFACE_TOKEN
   HYPERBOLIC_API_KEY
   KLUSTER_API_KEY
   MISTRAL_API_KEY
   NANOGPT_API_KEY
   NVIDIA_API_KEY
   OPENROUTER_KEY
   PERPLEXITY_API_KEY
   SAMBANOVA_API_KEY
   TOGETHERAI_API_KEY
   UNIFY_API_KEY
   XAI_API_KEY
   ```

   Optional for notifications:
   ```
   NOTIFICATION_WEBHOOK  # Slack/Discord webhook URL
   ```

2. **Workflow Configuration**

   The workflow is located at `.github/workflows/update-models.yml`

   **Schedule**: Runs every Monday at 00:00 UTC
   
   **Manual Trigger**: Can be triggered manually from GitHub Actions tab

3. **How It Works**

   - **On Success**: Changes are committed directly to main branch with notification
   - **On YAML Validation Failure**: Creates a PR for manual review and notifies @Berry-13
   - **On Script Failure**: Sends failure notification

5. **Customizing the Schedule**

   Edit `.github/workflows/update-models.yml`:
   ```yaml
   on:
     schedule:
       - cron: '0 0 * * 1'
   ```

   Examples:
   - Daily: `'0 0 * * *'`
   - Every 6 hours: `'0 */6 * * *'`
   - Monthly (1st of month): `'0 0 1 * *'`

### Notifications

The workflow sends notifications on:
- ✅ **Success**: Models updated and committed
- ⚠️ **YAML Validation Failed**: PR created for review
- ❌ **Failure**: Script encountered errors

Configure webhook URL in repository secrets as `NOTIFICATION_WEBHOOK`.

Supported formats:
- Slack incoming webhooks
- Discord webhooks
- Any webhook accepting JSON with `text` field

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