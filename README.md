# LibreChat Config Files aka `librechat.yaml` Collection
See the Custom Configuration Guide for more information: [LibreChat Custom Config Guide](https://www.librechat.ai/docs/configuration/librechat_yaml/setup)

## How to use
- Choose a file that corresponds to your needs
- Copy its **raw** URL (provided below)
- In your LibreChat `.env` file, add `CONFIG_PATH="https://raw-config-file-url/librechat.yaml"`
  - ⚠️ Replace the URL with one provided below!

## Available Configuration Files

| File Name | API Keys | File Strategy |
|-----------|----------|---------------|
| librechat-env-l.yaml | env | local |
| librechat-env-f.yaml | env | firebase |
| librechat-up-l.yaml | user_provided | local |
| librechat-up-f.yaml | user_provided | firebase |

## LibreChat Demo & Quick Deployments

<p align="left">
<a href="https://railway.app/template/b5k2mn?referralCode=HI9hWz">
  <img src="https://railway.app/button.svg" alt="Deploy on Railway">
</a>
</p>

## Contributions
Contributions are welcome!

**Important:** Instead of manually updating individual files, please use/update the scripts provided in the [scripts folder](./scripts/). See the [scripts README](./scripts/README.md) for more information on how to use these scripts for file generation and updates.

> **❗Note:**
> - Updates to the model list are always welcome
> - Adding endpoints requires also updating the scripts
> - Keep the APIs alphabetized
> - Provide a logo for new endpoints
> - When adding a new endpoint, add a note in the bottom of this README with the name and URL to get an API key
   
## File Descriptions
### `librechat-env-l.yaml`
Basic configuration:
- API Keys: .env variables
- File Strategy: `local`
- .env config:
  ```yaml
  CONFIG_PATH=https://raw.githubusercontent.com/LibreChat-AI/librechat-config-yaml/main/librechat-env-l.yaml
  AI302_API_KEY=
  APIPIE_API_KEY=
  COHERE_API_KEY=
  DEEPSEEK_API_KEY=
  FIREWORKS_API_KEY=
  GITHUB_TOKEN=
  GLHF_API_KEY
  GROQ_API_KEY=
  HUGGINGFACE_TOKEN=
  HYPERBOLIC_API_KEY=
  KLUSTER_API_KEY=
  MISTRAL_API_KEY=
  NANOGPT_API_KEY
  NVIDIA_API_KEY=
  OPENROUTER_KEY=
  PERPLEXITY_API_KEY=
  SAMBANOVA_API_KEY=
  TOGETHERAI_API_KEY=
  UNIFY_API_KEY=
  XAI_API_KEY=
  ```
### `librechat-env-f.yaml`
Basic configuration:
- API Keys: .env variables
- File Strategy: `firebase`
- .env config:
  ```yaml
  CONFIG_PATH=https://raw.githubusercontent.com/LibreChat-AI/librechat-config-yaml/main/librechat-env-f.yaml
  AI302_API_KEY=
  APIPIE_API_KEY=
  COHERE_API_KEY=
  DEEPSEEK_API_KEY=
  FIREWORKS_API_KEY=
  GITHUB_TOKEN=
  GLHF_API_KEY
  GROQ_API_KEY=
  HUGGINGFACE_TOKEN=
  HYPERBOLIC_API_KEY=
  KLUSTER_API_KEY=
  MISTRAL_API_KEY=
  NANOGPT_API_KEY
  NVIDIA_API_KEY=
  OPENROUTER_KEY=
  PERPLEXITY_API_KEY=
  SAMBANOVA_API_KEY=
  TOGETHERAI_API_KEY=
  UNIFY_API_KEY=
  XAI_API_KEY=
  ```

### `librechat-up-f.yaml`
Basic configuration:
- API Keys: `user_provided`
- File Strategy: `firebase`
- .env config:
  ```yaml
  CONFIG_PATH=https://raw.githubusercontent.com/LibreChat-AI/librechat-config-yaml/main/librechat-up-f.yaml
  ```

### `librechat-up-l.yaml`
Basic configuration:
- API Keys: `user_provided`
- File Strategy: `local`
- .env config:
  ```yaml
  CONFIG_PATH=https://raw.githubusercontent.com/LibreChat-AI/librechat-config-yaml/main/librechat-up-l.yaml
  ```

### `librechat-test.yaml`
- Personal file used to test changes and configs

---

## Get an API key:

| Provider | URL |
|----------|-----|
| 302.AI | https://302.ai/ |
| APIpie | https://apipie.ai/dashboard/profile/api-keys |
| Cohere | https://dashboard.cohere.com/api-keys |
| DeepSeek | https://platform.deepseek.com/api_keys |
| FireworksAI | https://fireworks.ai/ |
| Github Models | https://github.com |
| glhf.chat | https://glhf.chat |
| groq | https://console.groq.com/keys |
| HuggingFace | https://huggingface.co/settings/tokens |
| Hyperbolic | https://app.hyperbolic.xyz/ |
| Kluster | https://platform.kluster.ai/apikeys |
| Mistral | https://mistral.ai/ |
| NanoGPT | https://nano-gpt.com/api |
| NVIDIA | https://build.nvidia.com/explore/discover |
| OpenRouter | https://openrouter.ai/ |
| Perplexity | https://docs.perplexity.ai/docs/getting-started |
| SambaNova | https://cloud.sambanova.ai/apis |
| TogetherAI | https://www.together.ai/ |
| Unify | https://unify.ai/ |
| X.AI (Grok) | https://api.x.ai/ |
