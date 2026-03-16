import logging
from pathlib import Path
import convert_yaml_style
import update_models

from log_config import setup_logging

logger = logging.getLogger(__name__)

def get_user_choice(prompt):
    """Get user input with validation."""
    while True:
        choice = input(prompt).lower()
        if choice in ['y', 'n']:
            return choice == 'y'
        print("Please enter 'y' or 'n'")

def main(automated=False):
    setup_logging()
    if not automated:
        print("\nLibreChat YAML Configuration Update Tool")
        print("=======================================\n")

    try:
        if automated:
            # Automated mode: skip YAML style conversion, only update models
            logger.info("Running in automated mode")
            logger.info("Updating model lists in automated mode")
            update_models.main()
            logger.info("Model list updates completed")
        else:
            # Interactive mode
            # Ask about YAML style conversion
            if get_user_choice("Do you want to update YAML style formatting? (y/n): "):
                logger.info("Converting YAML style")
                convert_yaml_style.main()
                logger.info("YAML style conversion completed")
            else:
                logger.info("Skipping YAML style conversion")

            # Ask about model list updates
            if get_user_choice("Do you want to update model lists? (y/n): "):
                logger.info("Updating model lists")
                update_models.main()
                logger.info("Model list updates completed")
            else:
                logger.info("Skipping model list updates")

        if not automated:
            logger.info("All requested operations completed successfully")
        return 0

    except Exception as e:
        logger.error("Script failed: %s", e)
        if not automated:
            print(f"\nError: {str(e)}")
            print("Check the log file for details.")
        return 1

if __name__ == "__main__":
    import sys
    import os

    # Check for automated mode flags
    automated = '--automated' in sys.argv or os.getenv('AUTOMATED_MODE', '').lower() in ['true', '1', 'yes']

    exit_code = main(automated=automated)
    if exit_code != 0 and not automated:
        print("\nScript encountered errors. Please check the logs.")
