# LibreChat Config Files aka `librechat.yaml` Collection
See the Custom Configuration Guide for more information: [LibreChat Custom Config Guide](https://www.librechat.ai/docs/configuration/librechat_yaml/setup)

## How to use
- Choose a file that corresponds to your needs
- Copy its **raw** URL (provided below)
- In your LibreChat `.env` file, add `CONFIG_PATH="https://raw-config-file-url/librechat.yaml"`
  - ⚠️ Replace the URL with one provided below!

## Contributions
Contributions are welcome! Some files are more restrictive than others. Feel free to ask @fuegovic or @Berry here or on Discord if you have any questions or doubts.
- Updates to the model list are always welcome
- Adding endpoints is restricted on some files

> **❗Note:**
> - Keep the file content organized: Official APIs first, then Reverse Proxies
> - Keep the Official APIs alphabetized
> - Keep the Reverse Proxies alphabetized
> - Always provide a logo for new endpoints
> - When adding a new endpoint, always add a note in the bottom of this README with the name and URL to get an API key
>   - Use alphabetical order, like in the yaml files
>   - For reverse proxies on discord, add the invite link and the command to get the API key    

## File Descriptions
### `librechat.yaml`
Basic configuration:
- API Keys: .env variables
- File Strategy: `local`
- Fetch: true
- .env config:
  ```yaml
  CONFIG_PATH=https://raw.githubusercontent.com/LibreChat-AI/librechat-config-yaml/refs/heads/main/librechat.yaml
  APIPIE_API_KEY=
  COHERE_API_KEY=
  DEEPSEEK_API_KEY=
  FIREWORKS_API_KEY=
  GITHUB_TOKEN=
  GROQ_API_KEY=
  HUGGINGFACE_TOKEN=
  HYPERBOLIC_API_KEY=
  KLUSTER_API_KEY=
  MISTRAL_API_KEY=
  NVIDIA_API_KEY=
  OPENROUTER_KEY=
  PERPLEXITY_API_KEY=
  SAMBANOVA_API_KEY=
  TOGETHERAI_API_KEY=
  UNIFY_API_KEY=
  XAI_API_KEY=
  ```

### `librechat-hf.yaml`
Configuration used for the LibreChat Demo:
<p align="left">
  <a href="https://demo.librechat.cfd/">
      <img src="https://github.com/LibreChat-AI/librechat-config-yaml/assets/32828263/d3a1e88f-fce0-4a8e-8c1d-5901a3e1c2dd">
  <img href="https://demo.librechat.cfd/">
  </a>
</p>

- API Keys: Hardcoded as `user_provided`
- File Strategy: `firebase`
- Fetch: false
- .env config:
  ```yaml
  CONFIG_PATH=https://raw.githubusercontent.com/LibreChat-AI/librechat-config-yaml/refs/heads/main/librechat-hf.yaml
  ```

### `librechat-aio.yaml`
Same configuration used for the LibreChat Demo, but with firebase disable:

- Accepts: Official APIs and Reverse Proxies
- API Keys: Hardcoded as `user_provided`
- File Strategy: `local`
- Fetch: false
- .env config:
  ```yaml
  CONFIG_PATH=https://raw.githubusercontent.com/LibreChat-AI/librechat-config-yaml/refs/heads/main/librechat-aio.yaml
  ```

### `librechat-rw.yaml`
Configuration used for the Railway one-click install template:
<p align="left">
<a href="https://railway.app/template/b5k2mn?referralCode=HI9hWz">
  <img src="https://railway.app/button.svg" alt="Deploy on Railway">
</a>
</p>

- API Keys: .env variables
- File Strategy: `local`
- Fetch: false
- .env config:
  ```yaml
  CONFIG_PATH=https://raw.githubusercontent.com/LibreChat-AI/librechat-config-yaml/refs/heads/main/librechat-rw.yaml
  APIPIE_API_KEY=
  COHERE_API_KEY=
  DEEPSEEK_API_KEY=
  FIREWORKS_API_KEY=
  GITHUB_TOKEN=
  GROQ_API_KEY=
  HUGGINGFACE_TOKEN=
  HYPERBOLIC_API_KEY=
  KLUSTER_API_KEY=
  MISTRAL_API_KEY=
  NVIDIA_API_KEY=
  OPENROUTER_KEY=
  PERPLEXITY_API_KEY=
  SAMBANOVA_API_KEY=
  TOGETHERAI_API_KEY=
  UNIFY_API_KEY=
  XAI_API_KEY=
  ```

### `librechat-f.yaml`
- API Keys: .env variables
- File Strategy: `firebase`
- Fetch: false
- .env config:
  ```yaml
  CONFIG_PATH=https://raw.githubusercontent.com/LibreChat-AI/librechat-config-yaml/refs/heads/main/librechat-f.yaml
  APIPIE_API_KEY=
  COHERE_API_KEY=
  DEEPSEEK_API_KEY=
  FIREWORKS_API_KEY=
  GITHUB_TOKEN=
  GROQ_API_KEY=
  HUGGINGFACE_TOKEN=
  HYPERBOLIC_API_KEY=
  KLUSTER_API_KEY=
  MISTRAL_API_KEY=
  NVIDIA_API_KEY=
  OPENROUTER_KEY=
  PERPLEXITY_API_KEY=
  SAMBANOVA_API_KEY=
  TOGETHERAI_API_KEY=
  UNIFY_API_KEY=
  XAI_API_KEY=
  ```

### `librechat-test.yaml`
- Personal file used to test changes and configs

---

## Get an API key:

#### APIpie
- https://apipie.ai/dashboard/profile/api-keys

#### Cohere
- https://dashboard.cohere.com/api-keys

#### DeepSeek
- https://platform.deepseek.com/api_keys

#### FireworksAI
- https://fireworks.ai/

#### Github Models
- https://github.com

#### glhf.chat
- https://glhf.chat

#### groq
- https://console.groq.com/keys

#### HuggingFace
- https://huggingface.co/settings/tokens

#### Hyperbolic
- https://app.hyperbolic.xyz/

#### Kluster
- https://platform.kluster.ai/apikeys

#### Mistral
- https://mistral.ai/

#### NanoGPT
- https://nano-gpt.com/api

#### NVIDIA
- https://build.nvidia.com/explore/discover

#### OpenRouter
- https://openrouter.ai/

#### Perplexity
- https://docs.perplexity.ai/docs/getting-started

#### SambaNova
- https://cloud.sambanova.ai/apis

#### TogetherAI
- https://www.together.ai/

#### Unify
- https://unify.ai/

#### X.AI (Grok)
- https://api.x.ai/