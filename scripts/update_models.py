import json
from pathlib import Path
import importlib.util
import logging
from datetime import datetime
from ruamel.yaml import YAML
import yaml
import os

# Create logs directory if it doesn't exist
log_dir = Path(__file__).parent / 'logs'
log_dir.mkdir(exist_ok=True)

# Set up logger instance instead of basic config
logger = logging.getLogger('model_updater')
logger.setLevel(logging.DEBUG)

# Create log file with timestamp
log_file = log_dir / f'update_models_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'

# Create handlers with proper formatting
file_handler = logging.FileHandler(log_file)
console_handler = logging.StreamHandler()

# Set formatter
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Add handlers to logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Test logging
logger.info("Logging initialized successfully")

class UpdateStats:
    def __init__(self):
        self.provider_counts = {}  # Store model counts per provider
        self.failed_providers = []  # Store failed provider names
        self.updated_files = []    # Store successfully updated files
        self.failed_files = []     # Store files that failed to update

    def add_provider_result(self, provider_name, models):
        if models:
            self.provider_counts[provider_name] = len(models)
        else:
            self.failed_providers.append(provider_name)

    def add_file_result(self, filename, success):
        if success:
            self.updated_files.append(filename)
        else:
            self.failed_files.append(filename)

    def print_summary(self):
        summary = "\nUpdate Summary\n============="
        
        summary += "\n\nProvider Statistics:\n-----------------"
        if self.provider_counts:
            for provider, count in sorted(self.provider_counts.items()):
                summary += f"\n✓ {provider}: {count} models"
        
        if self.failed_providers:
            summary += "\n\nFailed Providers:\n----------------"
            for provider in sorted(self.failed_providers):
                summary += f"\n✗ {provider}"
        
        summary += "\n\nFile Updates:\n------------"
        if self.updated_files:
            for file in sorted(self.updated_files):
                summary += f"\n✓ {file}"
        
        if self.failed_files:
            summary += "\n\nFailed Files:\n-------------"
            for file in sorted(self.failed_files):
                summary += f"\n✗ {file}"

        summary += (f"\n\nSummary: {len(self.provider_counts)} providers updated, "
                    f"{len(self.failed_providers)} failed, "
                    f"{len(self.updated_files)} files updated, "
                    f"{len(self.failed_files)} files failed")
        
        logger.info(summary)  # Add logging for summary

def load_module_from_file(file_path, module_name):
    """Load a Python module from a file path."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def read_model_file(script_name):
    """Read and parse model data from output files with different formats."""
    try:
        output_file = Path(f"{script_name}.txt")
        if not output_file.exists():
            return None
            
        with open(output_file, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            
            # Handle empty files
            if not content:
                return None
                
            # Try to parse as JSON first
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                # If not JSON, process as line-based format
                lines = content.split('\n')
                # Clean up lines (remove quotes, commas, and whitespace)
                models = [line.strip(' ",\n') for line in lines if line.strip()]
                return models if models else None
                
    except Exception as e:
        logger.error(f"Error reading {script_name}.txt: {str(e)}")
        return None

def run_fetcher_script(script_name):
    """Run a model fetcher script and process its output."""
    try:
        script_path = Path(__file__).parent / f"{script_name}.py"
        logger.info(f"Attempting to run fetcher script: {script_path}")
        module = load_module_from_file(script_path, script_name)
        
        if hasattr(module, 'main'):
            logger.debug(f"Executing main() for {script_name}")
            module.main()
            result = read_model_file(script_name)
            logger.info(f"Fetcher {script_name} completed successfully")
            return result
    except Exception as e:
        logger.error(f"Error running {script_name}: {str(e)}", exc_info=True)
    return None

def clean_model_list(models):
    """Clean and validate the model list."""
    if not models:
        return None
        
    # If models is already a list of strings, return it
    if isinstance(models, list) and all(isinstance(m, str) for m in models):
        return models
        
    # If models is a dict or other structure, try to extract model names
    try:
        if isinstance(models, dict):
            # Handle case where models might be nested in a response
            if 'models' in models:
                models = models['models']
            # Handle case where models might be values in a dict
            elif any(isinstance(v, str) for v in models.values()):
                models = list(models.values())
            # Handle case where models might be keys in a dict
            else:
                models = list(models.keys())
        
        # Convert to list if it's some other iterable
        models = list(models)
        
        # Clean up each model name
        cleaned = []
        for model in models:
            if isinstance(model, (dict, list)):
                # Extract model name from complex structures
                if isinstance(model, dict) and 'id' in model:
                    cleaned.append(str(model['id']))
                elif isinstance(model, dict) and 'name' in model:
                    cleaned.append(str(model['name']))
            else:
                cleaned.append(str(model))
        
        return [m for m in cleaned if m]  # Remove any empty strings
        
    except Exception as e:
        logger.error(f"Error cleaning model list: {str(e)}")
        return None

def load_yaml_file(file_path):
    """Load a YAML file and return its contents while preserving formatting."""
    try:
        yaml = YAML()
        yaml.preserve_quotes = True
        yaml.width = 4096
        yaml.default_flow_style = False
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.load(f)
    except Exception as e:
        logger.error(f"Error loading YAML file {file_path}: {str(e)}")
        return None

def save_yaml_file(file_path, data):
    """Save data to a YAML file while preserving formatting."""
    try:
        yaml = YAML()
        yaml.preserve_quotes = True
        yaml.width = 4096
        yaml.default_flow_style = False
        yaml.indent(mapping=2, sequence=4, offset=2)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f)
        logger.info(f"Updated {file_path}")
    except Exception as e:
        logger.error(f"Error saving YAML file {file_path}: {str(e)}")

def update_yaml_models(yaml_data, provider_name, models):
    """Update the models list for a specific provider in the YAML data."""
    if not yaml_data or 'endpoints' not in yaml_data:
        return False

    # Clean and validate the model list
    cleaned_models = clean_model_list(models)
    if not cleaned_models:
        logger.error(f"No valid models found for {provider_name}")
        return False

    for endpoint in yaml_data['endpoints'].get('custom', []):
        if endpoint.get('name') == provider_name:
            endpoint['models']['default'] = cleaned_models
            endpoint['models']['fetch'] = False
            logger.info(f"Updated {len(cleaned_models)} models for {provider_name}")
            return True
    return False

def create_backup(yaml_path):
    """Create a backup of the YAML file with timestamp."""
    backup_path = yaml_path.with_suffix(f'.yaml.bak')
    
    try:
        # Read original content
        with open(yaml_path, 'r', encoding='utf-8') as source:
            content = source.read()
            
        # Write to backup with original content
        with open(backup_path, 'w', encoding='utf-8') as target:
            target.write(content)
            
        logger.info(f"Created backup at {backup_path}")
        return backup_path
    except Exception as e:
        logger.error(f"Error creating backup: {str(e)}")
        return None

def cleanup_temp_files():
    """Delete all temporary .txt files created by the fetcher scripts, except requirements.txt."""
    script_dir = Path(__file__).parent
    for txt_file in script_dir.glob("*.txt"):
        if txt_file.name == "requirements.txt":
            continue
        try:
            txt_file.unlink()
            logger.info(f"Deleted temporary file: {txt_file}")
        except Exception as e:
            logger.error(f"Error deleting {txt_file}: {str(e)}")

def update_models():
    # Get parent directory path
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Input and output file paths with parent directory
    input_files = [
        os.path.join(parent_dir, 'librechat-aio.yaml'),
        os.path.join(parent_dir, 'librechat-f.yaml'),
        os.path.join(parent_dir, 'librechat-hf.yaml'),
        os.path.join(parent_dir, 'librechat-rw.yaml'),
        os.path.join(parent_dir, 'librechat-test.yaml'),
        os.path.join(parent_dir, 'librechat.yaml'),
    ]

    # Load each input file and perform updates
    for input_file in input_files:
        if not os.path.exists(input_file):
            logger.warning(f"{input_file} not found, skipping...")
            continue

        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            # Make modifications here
            # ...existing code...

            # Save the updated file
            with open(input_file, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, sort_keys=False, allow_unicode=True)
                
            logger.info(f"Successfully updated {input_file}")

        except Exception as e:
            logger.error(f"Error processing {input_file}: {str(e)}")

def main():
    logger.info("Starting model update process")
    
    stats = UpdateStats()
    
    # Get parent directory path
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    yaml_files = [
        'librechat-aio.yaml',
        'librechat-f.yaml',
        'librechat-hf.yaml',
        'librechat-rw.yaml',
        'librechat-test.yaml',
        'librechat.yaml',
    ]
    
    # Define the scripts to run and their corresponding provider names
    fetchers = {
        'apipie': 'APIpie',
        'cohere': 'cohere',
        'deepseek': 'deepseek',
        'fireworks': 'Fireworks',
        'github': 'Github Models',
        'glhf': 'glhf.chat',
        'groq': 'groq',
        'huggingface': 'HuggingFace',
        'hyperbolic': 'Hyperbolic',
        'kluster': 'Kluster',
        'mistral': 'Mistral',
        'nanogpt': 'NanoGPT',
        'nvidia': 'Nvidia',
        'openrouter': 'OpenRouter',
        'perplexity': 'Perplexity',
        'sambanova': 'SambaNova',
        'togetherai': 'together.ai',
        'unify': 'Unify',
        'xai': 'xai'
    }
    
    # Fetch all models first
    logger.info("Fetching models from all providers...")
    provider_models = {}
    for script_name, provider_name in fetchers.items():
        logger.info(f"Running {script_name} fetcher")
        models = run_fetcher_script(script_name)
        
        if models:
            cleaned_models = clean_model_list(models)
            if cleaned_models:
                provider_models[provider_name] = cleaned_models
                stats.add_provider_result(provider_name, cleaned_models)
            else:
                stats.add_provider_result(provider_name, None)
        else:
            stats.add_provider_result(provider_name, None)
    
    # Now process each YAML file with the fetched models
    for yaml_file in yaml_files:
        yaml_path = Path(os.path.join(parent_dir, yaml_file))
        if not yaml_path.exists():
            stats.add_file_result(yaml_file, False)
            continue
            
        try:
            # Create initial backup of original file
            backup_path = create_backup(yaml_path)
            if not backup_path:
                stats.add_file_result(yaml_file, False)
                continue
            
            # Load YAML data
            yaml_data = load_yaml_file(yaml_path)
            if not yaml_data:
                stats.add_file_result(yaml_file, False)
                continue
            
            updates_made = False
            
            # Update YAML with previously fetched models
            for provider_name, models in provider_models.items():
                if update_yaml_models(yaml_data, provider_name, models):
                    updates_made = True
            
            # Save YAML file if updates were made
            if updates_made:
                save_yaml_file(yaml_path, yaml_data)
                stats.add_file_result(yaml_file, True)
            else:
                stats.add_file_result(yaml_file, False)
                
        except Exception as e:
            logger.error(f"Error processing {yaml_file}: {str(e)}")
            stats.add_file_result(yaml_file, False)

    # Clean up temporary files
    cleanup_temp_files()
    
    # Print summary
    stats.print_summary()
    
    logger.info("Model update process completed")
    
    # Return success if at least one file was updated
    return len(stats.updated_files) > 0

if __name__ == "__main__":
    try:
        success = main()
        logger.info(f"Script completed with success={success}")
        exit(0 if success else 1)
    except Exception as e:
        logger.critical("Unexpected error occurred", exc_info=True)
        exit(1)
