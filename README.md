# LibreChat Config Files aka `librechat.yaml` Collection
See the Custom Configuration Guide for more information: [LibreChat Custom Config Guide](https://docs.librechat.ai/install/configuration/custom_config.html)

## How to use
- Choose a file that corresponds to your needs
- Copy its **raw** URL (provided below)
- In your LibreChat `.env` file, add `CONFIG_PATH="https://raw-config-file-url/librechat.yaml"`
  - ⚠️ Replace the URL with the one provided below!

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
Basic configuration where model fetching is enabled on all endpoints that supports it:
- API Keys: .env variables
- File Strategy: `local`
- Fetch: true
- .env config:
  ```yaml
  CONFIG_PATH=https://raw.githubusercontent.com/fuegovic/lc-config-yaml/main/librechat.yaml
  ANYSCALE_API_KEY=
  APIPIE_API_KEY=
  COHERE_API_KEY=
  FIREWORKS_API_KEY=
  GROQ_API_KEY=
  MISTRAL_API_KEY=
  OPENROUTER_KEY=
  PERPLEXITY_API_KEY=
  SHUTTLEAI_API_KEY=
  TOGETHERAI_API_KEY=
  ```

### `librechat-hf.yaml`
Configuration used for the LibreChat Demo:
<p align="left">
  <a href="https://demo.librechat.cfd/">
      <img src="https://github.com/fuegovic/lc-config-yaml/assets/32828263/d3a1e88f-fce0-4a8e-8c1d-5901a3e1c2dd">
  <img href="https://demo.librechat.cfd/">
  </a>
</p>

- Accepts: Official APIs and Reverse Proxies
- API Keys: Hardcoded as `user_provided`
- File Strategy: `firebase`
- Fetch: false
- .env config:
  ```yaml
  CONFIG_PATH=https://raw.githubusercontent.com/fuegovic/lc-config-yaml/main/librechat-hf.yaml
  ```

### `librechat-aio.yaml`
Same configuration used for the LibreChat Demo, but with firebase disable:

- Accepts: Official APIs and Reverse Proxies
- API Keys: Hardcoded as `user_provided`
- File Strategy: `local`
- Fetch: false
- .env config:
  ```yaml
  CONFIG_PATH=https://raw.githubusercontent.com/fuegovic/lc-config-yaml/main/librechat-aio.yaml
  ```

### `librechat-rw.yaml`
Configuration used for the Railway one-click install template:
<p align="left">
<a href="https://railway.app/template/b5k2mn?referralCode=HI9hWz">
  <img src="https://railway.app/button.svg" alt="Deploy on Railway">
</a>
</p>

- Accepts: Official APIs
- API Keys: .env variables
- File Strategy: `local`
- Fetch: false
- .env config:
  ```yaml
  CONFIG_PATH=https://raw.githubusercontent.com/fuegovic/lc-config-yaml/main/librechat-rw.yaml
  ANYSCALE_API_KEY=
  APIPIE_API_KEY=
  COHERE_API_KEY=
  FIREWORKS_API_KEY=
  GROQ_API_KEY=
  MISTRAL_API_KEY=
  OPENROUTER_KEY=
  PERPLEXITY_API_KEY=
  SHUTTLEAI_API_KEY=
  TOGETHERAI_API_KEY=
  ```
- Note:
  - Accepts `model` updates
  - Contact @Berry or @fuegovic here or on Discord before submitting a PR to add a new `endpoint`

### `librechat-f.yaml`
- Accepts: Official APIs
- API Keys: .env variables
- File Strategy: `firebase`
- Fetch: false
- .env config:
  ```yaml
  CONFIG_PATH=https://raw.githubusercontent.com/fuegovic/lc-config-yaml/main/librechat-f.yaml
  ANYSCALE_API_KEY=
  APIPIE_API_KEY=
  COHERE_API_KEY=
  FIREWORKS_API_KEY=
  GROQ_API_KEY=
  MISTRAL_API_KEY=
  OPENROUTER_KEY=
  PERPLEXITY_API_KEY=
  SHUTTLEAI_API_KEY=
  TOGETHERAI_API_KEY=
  ```

### `librechat-test.yaml`
- Personal file used to test changes and configs

---

## Get an API key:


### Official APIs:

#### Anyscale
- https://app.endpoints.anyscale.com/credentials

#### APIpie
- https://apipie.ai/dashboard/profile/api-keys

#### Cohere
- https://dashboard.cohere.com/api-keys

#### FireworksAI
- https://fireworks.ai/

#### groq
- https://console.groq.com/keys

#### Mistral
- https://mistral.ai/

#### OpenRouter
- https://openrouter.ai/

#### ShuttleAI
- https://shuttleai.app/keys

#### TogetherAI
- https://www.together.ai/

---

### Reverse Proxies:

#### ConvoAI
- https://discord.gg/taH8UnARwd
- Get API key on discord with the command `/key`

#### FreeGPT-4
- https://discord.com/invite/gpt4
- Get API key on discord with the command `/key`

#### Hyzenberg
- https://discord.gg/ECUEFQzATa
- Get API key on discord with the command `/key get`

#### Mandrill
- https://discord.mandrillai.tech
- Get API key on discord with the command `/key get` 

#### NagaAI
- https://discord.naga.ac
- Get API key on discord with the command `/key get` 

#### Pawan
- https://discord.gg/pawan
- Get API key on discord with the command `/key`

#### Shard
- https://discord.gg/ligma
- Get API key on discord with the command `/get-key`

#### Zukijourney
- https://discord.gg/zukijourney
- Get API key on discord with the command `/key`
