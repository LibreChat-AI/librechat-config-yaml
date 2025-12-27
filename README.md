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
> - Adding endpoints requires also updating the scripts
> - Keep the APIs alphabetized
> - Provide a logo for new endpoints
> - When adding a new endpoint, add a note in the bottom of this README with the name and URL to get an API key

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
