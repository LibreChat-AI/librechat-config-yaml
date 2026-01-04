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

## GitHub Actions (Automated Daily Updates)

This repository includes automated daily model updates via GitHub Actions.

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

   Optional for Railway auto-redeployment (see [Railway Integration](#railway-integration)):
   ```
   RAILWAY_TOKEN
   RAILWAY_PROJECT_ID
   RAILWAY_ENVIRONMENT_ID
   RAILWAY_SERVICE_ID
   ```

2. **Workflow Configuration**

   The workflow is located at `.github/workflows/update-models.yml`

   **Schedule**: Runs every day at 00:00 UTC
   
   **Manual Trigger**: Can be triggered manually from GitHub Actions tab

3. **How It Works**

   - **On Success**: Changes are committed directly to main branch with notification
   - **On YAML Validation Failure**: Creates a PR for manual review and notifies @Berry-13
   - **On Script Failure**: Sends failure notification
   - **Railway Redeployment**: After successful commit, triggers Railway redeployment (if configured)

4. **Railway Redeployment**

   After model updates are committed, the workflow can automatically trigger a Railway redeployment:

   - **Enable/Disable**: Set repository variable `RAILWAY_REDEPLOY` to `true` or `false` (defaults to `true`)
   - **Requirements**: All four Railway secrets must be configured
   - **Behavior**: Skips silently if `RAILWAY_TOKEN` is not set

5. **Customizing the Schedule**

   Edit `.github/workflows/update-models.yml`:
   ```yaml
   on:
     schedule:
       - cron: '0 0 * * *'
   ```

   Examples:
   - Weekly (Mondays): `'0 0 * * 1'`
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

## Railway Integration

Automatically redeploy your LibreChat instance on Railway after model list updates.

### Overview

The [`railway_redeploy.py`](railway_redeploy.py) script uses the Railway GraphQL API to trigger a redeployment of your LibreChat service whenever model lists are updated.

### Required Environment Variables

```bash
# Railway API Token - https://railway.app/account/tokens
RAILWAY_TOKEN=your-railway-api-token

# Project ID - Found in your Railway project URL or settings
RAILWAY_PROJECT_ID=your-project-id

# Environment ID - The deployment environment (e.g., production)
RAILWAY_ENV_ID=your-environment-id

# Service ID - The specific service to redeploy
RAILWAY_SERVICE_ID=your-service-id
```

### How to Obtain Railway Values

1. **RAILWAY_TOKEN**
   - Go to [Railway Account Tokens](https://railway.app/account/tokens)
   - Create a new token with appropriate permissions
   - Copy the token value

2. **RAILWAY_PROJECT_ID**
   - Open your project in Railway dashboard
   - The project ID is in the URL: `https://railway.app/project/<PROJECT_ID>`
   - Or find it in Project Settings → General

3. **RAILWAY_ENV_ID**
   - In your project, go to Settings → Environments
   - Click on the environment you want to deploy to
   - The environment ID is in the URL or settings panel

4. **RAILWAY_SERVICE_ID**
   - Click on your service in the Railway dashboard
   - The service ID is in the URL: `https://railway.app/project/<PROJECT_ID>/service/<SERVICE_ID>`

### GitHub Actions Configuration

To enable Railway redeployment in the automated workflow:

1. Add the four Railway secrets to your repository (Settings → Secrets → Actions)
2. Optionally set the `RAILWAY_REDEPLOY` repository variable:
   - Go to Settings → Secrets and variables → Actions → Variables
   - Add `RAILWAY_REDEPLOY` with value `true` (enabled) or `false` (disabled)
   - Default is `true` if not set

### Manual Usage

Run the redeployment script locally:

```bash
cd scripts
python railway_redeploy.py
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
│   ├── ai302.py               # Fetch models from 302.AI
│   ├── apipie.py              # Fetch models from APIpie
│   ├── cohere.py              # Fetch models from Cohere
│   ├── deepseek.py            # Fetch models from Deepseek
│   ├── fireworks.py           # Fetch models from Fireworks
│   ├── github.py              # Fetch models from Github Models
│   ├── glhf.py                # Fetch models from GLHF.chat
│   ├── groq.py                # Fetch models from Groq
│   ├── huggingface.py         # Fetch models from HuggingFace
│   ├── hyperbolic.py          # Fetch models from Hyperbolic
│   ├── kluster.py             # Fetch models from Kluster
│   ├── mistral.py             # Fetch models from Mistral
│   ├── nanogpt.py             # Fetch models from NanoGPT
│   ├── nvidia.py              # Fetch models from Nvidia
│   ├── openrouter.py          # Fetch models from OpenRouter
│   ├── perplexity.py          # Fetch models from Perplexity
│   ├── sambanova.py           # Fetch models from SambaNova
│   ├── togetherai.py          # Fetch models from Together.ai
│   ├── unify.py               # Fetch models from Unify
│   └── xai.py                 # Fetch models from XAI
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
- 302.AI
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

## Provider Script Validation Status

The provider scripts have been analyzed against their official API documentation:

| Status | Count | Providers |
|--------|-------|-----------|
| ✅ Validated | 11 | Cohere, DeepSeek, Fireworks, GitHub, Groq, HuggingFace, Mistral, NVIDIA, OpenRouter, TogetherAI, xAI |
| ⚠️ Issues Found | 4 | APIpie (minor), NanoGPT, Perplexity, SambaNova |
| ❓ Cannot Verify | 5 | 302.AI, GLHF, Hyperbolic, Kluster, Unify |

### Key Findings

- **Perplexity & SambaNova**: Use web scraping instead of APIs (fragile, may break if page structure changes)
- **Unify**: Uses `/v0/` API version (potentially experimental)
- **5 providers**: Lack public API documentation for verification
- **Most scripts**: Well-implemented with proper authentication and error handling

### Detailed Status

#### ✅ Validated Scripts
These scripts have been verified against official API documentation and use proper API endpoints:

| Provider | Script | API Endpoint |
|----------|--------|--------------|
| Cohere | [`cohere.py`](cohere.py) | `https://api.cohere.com/v1/models` |
| DeepSeek | [`deepseek.py`](deepseek.py) | `https://api.deepseek.com/models` |
| Fireworks | [`fireworks.py`](fireworks.py) | `https://api.fireworks.ai/inference/v1/models` |
| GitHub | [`github.py`](github.py) | `https://models.inference.ai.azure.com/models` |
| Groq | [`groq.py`](groq.py) | `https://api.groq.com/openai/v1/models` |
| HuggingFace | [`huggingface.py`](huggingface.py) | `https://huggingface.co/api/models` |
| Mistral | [`mistral.py`](mistral.py) | `https://api.mistral.ai/v1/models` |
| NVIDIA | [`nvidia.py`](nvidia.py) | `https://integrate.api.nvidia.com/v1/models` |
| OpenRouter | [`openrouter.py`](openrouter.py) | `https://openrouter.ai/api/v1/models` |
| TogetherAI | [`togetherai.py`](togetherai.py) | `https://api.together.xyz/v1/models` |
| xAI | [`xai.py`](xai.py) | `https://api.x.ai/v1/models` |

#### ⚠️ Scripts with Issues

| Provider | Issue | Impact |
|----------|-------|--------|
| APIpie | Minor: No official docs found, but uses standard OpenAI-compatible endpoint | Low |
| NanoGPT | Web scraping from `nano-gpt.com/api` | May break if page changes |
| Perplexity | Scrapes documentation page instead of API | Fragile, may break |
| SambaNova | Scrapes community docs instead of API | Fragile, may break |

#### ❓ Cannot Verify

These providers lack public API documentation:
- **302.AI** - No public API docs available
- **GLHF** - No public API docs available
- **Hyperbolic** - No public API docs available
- **Kluster** - No public API docs available
- **Unify** - Uses `/v0/` endpoint (experimental)

## Testing Limitations

### API Key Requirements

Most provider scripts require valid API keys for testing:

| Provider | Key Required | Notes |
|----------|--------------|-------|
| NVIDIA | ❌ No | Public API |
| OpenRouter | ❌ No | Public API |
| Cohere | ✅ Yes | Free tier available |
| DeepSeek | ✅ Yes | - |
| Fireworks | ✅ Yes | - |
| GitHub | ✅ Yes | Uses `GITHUB_TOKEN` |
| Groq | ✅ Yes | Free tier available |
| HuggingFace | ✅ Yes | Free tier available |
| Mistral | ✅ Yes | - |
| TogetherAI | ✅ Yes | - |
| xAI | ✅ Yes | - |

### Web Scraping Scripts

The following scripts use web scraping instead of official APIs and may break if the source website changes:

| Provider | Source URL | Risk Level |
|----------|------------|------------|
| NanoGPT | `nano-gpt.com/api` | Medium |
| Perplexity | Documentation page | High |
| SambaNova | Community docs | High |

**Recommendation**: Monitor these scripts for failures and consider implementing official API calls when documentation becomes available.

### Unverifiable Providers

The following providers could not be verified due to lack of public API documentation:

- **302.AI** ([`ai302.py`](ai302.py))
- **GLHF** ([`glhf.py`](glhf.py))
- **Hyperbolic** ([`hyperbolic.py`](hyperbolic.py))
- **Kluster** ([`kluster.py`](kluster.py))
- **Unify** ([`unify.py`](unify.py)) - Uses experimental `/v0/` API

These scripts appear functional based on code review but cannot be validated against official specifications.

## Contributing

When adding new providers:
1. Create a new fetcher script in the scripts directory
2. Update the provider list in `update_models.py`
3. Add any required API keys to `.env.example`
4. Document the API endpoint and any authentication requirements
5. Prefer official APIs over web scraping when available