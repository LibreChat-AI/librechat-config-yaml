#!/usr/bin/env python3
"""
Automated Model Update Script for GitHub Actions
Fetches latest models from all providers and updates YAML files with validation.
"""

import sys
import os
import logging
from pathlib import Path
from ruamel.yaml import YAML
import update_models

# Set up logging
log_dir = Path(__file__).parent / 'logs'
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'automated_update.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def validate_yaml_file(file_path):
    """
    Validate YAML file can be parsed correctly.
    
    Args:
        file_path: Path to YAML file to validate
        
    Returns:
        tuple: (is_valid, error_message)
    """
    try:
        yaml = YAML()
        yaml.preserve_quotes = True
        yaml.width = 4096
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = yaml.load(f)
            
        if content is None:
            return False, "YAML file is empty"
            
        if not isinstance(content, dict):
            return False, "YAML file does not contain a valid dictionary structure"
            
        # Check for required keys in LibreChat config
        required_keys = ['version', 'endpoints']
        missing_keys = [key for key in required_keys if key not in content]
        if missing_keys:
            return False, f"Missing required keys: {', '.join(missing_keys)}"
            
        logger.info(f"YAML validation successful for {file_path}")
        return True, None
        
    except Exception as e:
        error_msg = f"YAML parsing error: {str(e)}"
        logger.error(error_msg)
        return False, error_msg


def main():
    """Main function for automated updates."""
    logger.info("=" * 70)
    logger.info("Starting automated model update process")
    logger.info("=" * 70)
    
    try:
        # Get configuration from environment
        logger.info("Running in FULL mode - updating all YAML files")
        
        # Run the model update
        logger.info("Fetching latest models from all providers...")
        success = update_models.main()
        
        if not success:
            logger.error("Model update failed")
            return 1
            
        logger.info("Model update completed successfully")
        
        # Validate YAML files after update
        logger.info("Validating updated YAML files...")
        
        parent_dir = Path(__file__).parent.parent
        
        files_to_validate = [
            parent_dir / 'librechat-env-f.yaml',
            parent_dir / 'librechat-env-l.yaml',
            parent_dir / 'librechat-up-f.yaml',
            parent_dir / 'librechat-up-l.yaml',
            parent_dir / 'librechat-test.yaml',
        ]
        
        validation_failed = False
        validation_errors = []
        
        for yaml_file in files_to_validate:
            if yaml_file.exists():
                is_valid, error = validate_yaml_file(yaml_file)
                if not is_valid:
                    validation_failed = True
                    validation_errors.append(f"{yaml_file.name}: {error}")
                    logger.error(f"Validation failed for {yaml_file.name}: {error}")
                else:
                    logger.info(f"✓ {yaml_file.name} validated successfully")
        
        if validation_failed:
            logger.error("=" * 70)
            logger.error("YAML VALIDATION FAILED")
            logger.error("=" * 70)
            for error in validation_errors:
                logger.error(f"  - {error}")
            logger.error("=" * 70)
            
            # Set environment variable to signal GitHub Actions
            # This will be checked by the workflow to decide whether to create a PR
            with open(os.environ.get('GITHUB_ENV', '/dev/null'), 'a') as env_file:
                env_file.write("YAML_VALIDATION_FAILED=true\n")
                env_file.write(f"VALIDATION_ERRORS={'; '.join(validation_errors)}\n")
            
            return 2  # Exit code 2 indicates validation failure
        
        logger.info("=" * 70)
        logger.info("All YAML files validated successfully")
        logger.info("Automated update completed successfully")
        logger.info("=" * 70)
        
        return 0
        
    except Exception as e:
        logger.critical(f"Unexpected error in automated update: {str(e)}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)