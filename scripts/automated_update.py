#!/usr/bin/env python3
"""
Automated Model Update Script for GitHub Actions
Fetches latest models from all providers and updates YAML files with validation.
"""

import sys
import os
import logging
from pathlib import Path
import update_models
from update_models import validate_yaml_file

from log_config import setup_logging

logger = logging.getLogger(__name__)


def main():
    """Main function for automated updates."""
    setup_logging()
    logger.info("=" * 70)
    logger.info("Starting automated model update process")
    logger.info("=" * 70)

    try:
        # Get configuration from environment
        logger.info("Running in FULL mode - updating all YAML files")

        # Run the model update
        logger.info("Fetching latest models from all providers...")
        stats = update_models.main()

        if stats is None or len(stats.updated_files) == 0:
            logger.error("Model update failed or no files updated")
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
                    validation_errors.append("%s: %s" % (yaml_file.name, error))
                    logger.error("Validation failed for %s: %s", yaml_file.name, error)
                else:
                    logger.info("[OK] %s validated successfully", yaml_file.name)

        if validation_failed:
            logger.error("=" * 70)
            logger.error("YAML VALIDATION FAILED")
            logger.error("=" * 70)
            for error in validation_errors:
                logger.error("  - %s", error)
            logger.error("=" * 70)

            # Set environment variable to signal GitHub Actions
            # This will be checked by the workflow to decide whether to create a PR
            with open(os.environ.get('GITHUB_ENV', '/dev/null'), 'a') as env_file:
                env_file.write("YAML_VALIDATION_FAILED=true\n")
                env_file.write("VALIDATION_ERRORS=%s\n" % '; '.join(validation_errors))

            return 2  # Exit code 2 indicates validation failure

        logger.info("=" * 70)
        logger.info("All YAML files validated successfully")
        logger.info("Automated update completed successfully")
        logger.info("=" * 70)

        # Write commit message for CI workflow
        msg_path = Path(__file__).parent.parent / ".commit_msg"
        try:
            msg_path.write_text(stats.generate_commit_message(), encoding="utf-8")
            logger.info("Commit message written to %s", msg_path)
        except Exception as e:
            logger.warning("Failed to write commit message: %s", e)

        return 0

    except Exception as e:
        logger.critical("Unexpected error in automated update: %s", e, exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
