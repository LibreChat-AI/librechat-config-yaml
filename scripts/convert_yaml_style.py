from ruamel.yaml import YAML
from pathlib import Path
import logging
import shutil
import os

from log_config import setup_logging

logger = logging.getLogger(__name__)

def create_backup(file_path):
    """Create a backup of the original file."""
    try:
        backup_path = file_path.with_suffix(f'.yaml.bak')
        shutil.copy2(file_path, backup_path)  # Use copy2 to preserve metadata
        logger.info("Created backup at %s", backup_path)
        return backup_path
    except Exception as e:
        logger.error("Backup creation failed: %s", e)
        raise

def convert_yaml_style():
    """Convert YAML arrays from flow style to block style while preserving mapping indentation."""
    # Get parent directory path
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Input files with parent directory
    yaml_files = [
        os.path.join(parent_dir, 'librechat-env-f.yaml'),
        os.path.join(parent_dir, 'librechat-env-l.yaml'),
        os.path.join(parent_dir, 'librechat-up-f.yaml'),
        os.path.join(parent_dir, 'librechat-up-l.yaml'),
        os.path.join(parent_dir, 'librechat-test.yaml'),
    ]

    for filename in yaml_files:
        if not os.path.exists(filename):
            logger.warning("%s not found, skipping...", filename)
            continue

        try:
            # Initialize YAML parser with specific settings
            yaml = YAML()
            yaml.preserve_quotes = True
            yaml.width = 4096
            yaml.default_flow_style = False

            # Configure indentation
            yaml.indent(mapping=2, sequence=4, offset=2)
            yaml.sequence_dash_offset = 2

            # Read and parse YAML
            with open(filename, 'r', encoding='utf-8') as f:
                data = yaml.load(f)

            if data is None:
                raise ValueError("No YAML content could be loaded")

            # Function to recursively convert sequences to block style
            def convert_to_block_style(node):
                if isinstance(node, list):
                    # Force block style for sequences
                    if hasattr(node, 'fa'):
                        node.fa.set_block_style()
                    # Recursively process list items
                    for item in node:
                        convert_to_block_style(item)
                elif isinstance(node, dict):
                    # Process dictionary values
                    for value in node.values():
                        convert_to_block_style(value)

            # Convert all sequences to block style
            convert_to_block_style(data)

            # Create backup before modifying
            create_backup(Path(filename))

            # Save with corrected formatting
            with open(filename, 'w', encoding='utf-8') as f:
                yaml.dump(data, f)

            logger.info("Successfully converted %s", filename)

        except Exception as e:
            logger.error("Error converting file %s: %s", filename, e)
            continue

def main():
    setup_logging()
    try:
        logger.info("Starting conversion of YAML files")
        convert_yaml_style()
        logger.info("Conversion completed")

    except Exception as e:
        logger.error("Script failed: %s", e, exc_info=True)
        return 1
    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        logger.info("Script completed with exit_code=%d", exit_code)
        exit(exit_code)
    except Exception as e:
        logger.critical("Unexpected error occurred", exc_info=True)
        exit(1)
