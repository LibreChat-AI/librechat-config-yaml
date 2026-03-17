from pathlib import Path
import logging
from ruamel.yaml import YAML
import os

from log_config import setup_logging
from providers import discover_providers, FetchStatus

logger = logging.getLogger(__name__)

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
                summary += "\n[OK] %s: %d models" % (provider, count)

        if self.failed_providers:
            summary += "\n\nFailed Providers:\n----------------"
            for provider in sorted(self.failed_providers):
                summary += "\n[FAIL] %s" % provider

        summary += "\n\nFile Updates:\n------------"
        if self.updated_files:
            for file in sorted(self.updated_files):
                summary += "\n[OK] %s" % file

        if self.failed_files:
            summary += "\n\nFailed Files:\n-------------"
            for file in sorted(self.failed_files):
                summary += "\n[FAIL] %s" % file

        summary += ("\n\nSummary: %d providers updated, "
                    "%d failed, "
                    "%d files updated, "
                    "%d files failed" % (len(self.provider_counts),
                    len(self.failed_providers),
                    len(self.updated_files),
                    len(self.failed_files)))

        logger.info(summary)  # Add logging for summary

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
        logger.error("Error loading YAML file %s: %s", file_path, e)
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
        logger.info("Updated %s", file_path)
    except Exception as e:
        logger.error("Error saving YAML file %s: %s", file_path, e)

def update_yaml_models(yaml_data, provider_name, models):
    """Update the models list for a specific provider in the YAML data."""
    if not yaml_data or 'endpoints' not in yaml_data:
        return False

    if not models:
        logger.error("No valid models found for %s", provider_name)
        return False

    for endpoint in yaml_data['endpoints'].get('custom', []):
        if endpoint.get('name') == provider_name:
            endpoint['models']['default'] = models
            endpoint['models']['fetch'] = False
            logger.info("Updated %d models for %s", len(models), provider_name)
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

        logger.info("Created backup at %s", backup_path)
        return backup_path
    except Exception as e:
        logger.error("Error creating backup: %s", e)
        return None

def cleanup_temp_files():
    """Delete all temporary .txt files created by the fetcher scripts, except requirements.txt."""
    script_dir = Path(__file__).parent
    for txt_file in script_dir.glob("*.txt"):
        if txt_file.name == "requirements.txt":
            continue
        try:
            txt_file.unlink()
            logger.info("Deleted temporary file: %s", txt_file)
        except Exception as e:
            logger.error("Error deleting %s: %s", txt_file, e)

def main():
    setup_logging()
    logger.info("Starting model update process")

    stats = UpdateStats()

    # Get parent directory path
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    yaml_files = [
        'librechat-env-f.yaml',
        'librechat-env-l.yaml',
        'librechat-up-f.yaml',
        'librechat-up-l.yaml',
        'librechat-test.yaml',
        # 'librechat.yaml',
    ]

    # Fetch all models from contract-based providers
    logger.info("Fetching models from all providers...")
    provider_models = {}

    registry = discover_providers()
    logger.info("Discovered %d contract-based providers: %s", len(registry), list(registry.keys()))

    for provider_name, fetcher_cls in registry.items():
        logger.info("Running %s fetcher", provider_name)
        fetcher = fetcher_cls()
        result = fetcher.run()
        if result.status == FetchStatus.SUCCESS:
            provider_models[result.provider_name] = result.models
            stats.add_provider_result(result.provider_name, result.models)
            logger.info("%s: %s (%d models)", result.provider_name, result.status.value, result.model_count)
        else:
            logger.warning("%s: %s - %s", result.provider_name, result.status.value, result.error_message)
            stats.add_provider_result(result.provider_name, None)

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
            logger.error("Error processing %s: %s", yaml_file, e)
            stats.add_file_result(yaml_file, False)

    # Clean up temporary files
    cleanup_temp_files()

    # Print summary
    stats.print_summary()

    logger.info("Model update process completed")

    # Return success if at least one file was updated
    return len(stats.updated_files) > 0

if __name__ == "__main__":
    import sys

    try:
        success = main()
        logger.info("Script completed with success=%s", success)
        exit(0 if success else 1)
    except Exception as e:
        logger.critical("Unexpected error occurred", exc_info=True)
        exit(1)
