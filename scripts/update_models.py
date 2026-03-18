from datetime import datetime, timezone
from pathlib import Path
import logging
import os
import tempfile

from ruamel.yaml import YAML

from log_config import setup_logging
from providers import discover_providers, FetchStatus

logger = logging.getLogger(__name__)

STALENESS_THRESHOLD = float(os.environ.get("STALENESS_THRESHOLD", "0.5"))


def check_staleness(provider_name, new_models, yaml_data):
    """Check if new model count is suspiciously low compared to existing.

    Returns:
        tuple: (is_stale, old_count, new_count)
    """
    if not yaml_data or 'endpoints' not in yaml_data:
        return False, 0, len(new_models)

    for endpoint in yaml_data['endpoints'].get('custom', []):
        if endpoint.get('name') == provider_name:
            existing = endpoint.get('models', {}).get('default', [])
            old_count = len(existing)
            new_count = len(new_models)

            if old_count == 0:
                return False, 0, new_count

            ratio = new_count / old_count
            if ratio < STALENESS_THRESHOLD:
                return True, old_count, new_count
            return False, old_count, new_count

    return False, 0, len(new_models)


class UpdateStats:
    def __init__(self):
        self.provider_results = {}  # name -> (old_count, new_count)
        self.failed_providers = {}  # name -> error_message
        self.stale_providers = []   # (name, old_count, new_count) tuples
        self.updated_files = []     # Successfully updated files
        self.failed_files = []      # Files that failed to update

    def add_provider_result(self, provider_name, old_count, new_count):
        self.provider_results[provider_name] = (old_count, new_count)

    def add_failed_provider(self, provider_name, error_message):
        self.failed_providers[provider_name] = error_message or "unknown error"

    def add_stale_provider(self, provider_name, old_count, new_count):
        self.stale_providers.append((provider_name, old_count, new_count))

    def add_file_result(self, filename, success):
        if success:
            self.updated_files.append(filename)
        else:
            self.failed_files.append(filename)

    def print_summary(self):
        summary = "\nUpdate Summary\n============="

        summary += "\n\nProvider Statistics:\n-----------------"
        if self.provider_results:
            for provider, (old, new) in sorted(self.provider_results.items()):
                delta = new - old
                if delta >= 0:
                    sign = "+"
                else:
                    sign = ""
                summary += "\n[OK] %s: %d models (%s%d)" % (provider, new, sign, delta)

        if self.failed_providers:
            summary += "\n\nFailed Providers:\n----------------"
            for provider in sorted(self.failed_providers):
                summary += "\n[FAIL] %s: %s" % (provider, self.failed_providers[provider])

        if self.stale_providers:
            summary += "\n\nStale Providers (skipped):\n-------------------------"
            for provider, old, new in sorted(self.stale_providers):
                summary += "\n[SKIP] %s: %d -> %d models (below threshold)" % (provider, old, new)

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
                    "%d stale (skipped), "
                    "%d files updated, "
                    "%d files failed" % (len(self.provider_results),
                    len(self.failed_providers),
                    len(self.stale_providers),
                    len(self.updated_files),
                    len(self.failed_files)))

        logger.info(summary)

    def generate_commit_message(self):
        """Generate a commit message with subject and body."""
        subject = self._commit_subject()
        body = self._commit_body()
        return "%s\n\n%s" % (subject, body)

    def _commit_subject(self):
        """Build commit subject line with provider deltas."""
        deltas = []
        for provider, (old, new) in sorted(self.provider_results.items()):
            diff = new - old
            if diff > 0:
                deltas.append("%s +%d" % (provider, diff))
            elif diff < 0:
                deltas.append("%s %d" % (provider, diff))

        if not deltas:
            date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            return "chore: update models (%s)" % date_str

        subject = "chore: update models (%s)" % ", ".join(deltas)
        if len(subject) <= 72:
            return subject

        # Truncate: count gained vs lost
        gained = 0
        lost = 0
        for provider, (old, new) in self.provider_results.items():
            diff = new - old
            if diff > 0:
                gained += 1
            elif diff < 0:
                lost += 1

        parts = []
        if gained:
            parts.append("%d providers gained models" % gained)
        if lost:
            parts.append("%d lost models" % lost)
        return "chore: update models (%s)" % ", ".join(parts)

    def _commit_body(self):
        """Build commit body with provider details."""
        lines = []

        if self.provider_results:
            for provider, (old, new) in sorted(self.provider_results.items()):
                delta = new - old
                if delta >= 0:
                    sign = "+"
                else:
                    sign = ""
                lines.append("%s: %d -> %d (%s%d)" % (provider, old, new, sign, delta))

        if self.failed_providers:
            lines.append("")
            lines.append("Failed:")
            for provider in sorted(self.failed_providers):
                lines.append("  %s: %s" % (provider, self.failed_providers[provider]))

        if self.stale_providers:
            lines.append("")
            lines.append("Stale (skipped):")
            for provider, old, new in sorted(self.stale_providers):
                lines.append("  %s: %d -> %d" % (provider, old, new))

        return "\n".join(lines)

def validate_yaml_file(file_path):
    """Validate YAML file can be parsed correctly.

    Args:
        file_path: Path to YAML file to validate

    Returns:
        tuple: (is_valid, error_message)
    """
    try:
        yaml = YAML()
        yaml.preserve_quotes = True
        yaml.width = 4096
        yaml.default_flow_style = False
        yaml.indent(mapping=2, sequence=4, offset=2)

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
            return False, "Missing required keys: %s" % ', '.join(missing_keys)

        logger.info("YAML validation successful for %s", file_path)
        return True, None

    except Exception as e:
        error_msg = "YAML parsing error: %s" % e
        logger.error("%s", error_msg)
        return False, error_msg


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
    """Save data to a YAML file atomically with validation."""
    file_path = Path(file_path)
    tmp_fd = None
    tmp_path = None

    try:
        yaml = YAML()
        yaml.preserve_quotes = True
        yaml.width = 4096
        yaml.default_flow_style = False
        yaml.indent(mapping=2, sequence=4, offset=2)

        # Create temp file in same directory (same filesystem = atomic rename)
        tmp_fd, tmp_path = tempfile.mkstemp(
            suffix='.yaml.tmp',
            dir=str(file_path.parent),
        )

        # Write to temp file
        with os.fdopen(tmp_fd, 'w', encoding='utf-8') as f:
            tmp_fd = None  # os.fdopen takes ownership of fd
            yaml.dump(data, f)
            f.flush()
            os.fsync(f.fileno())

        # Validate the temp file before replacing
        is_valid, error = validate_yaml_file(tmp_path)
        if not is_valid:
            raise ValueError(
                "Validation failed for %s: %s" % (file_path.name, error)
            )

        # Atomic replace
        os.replace(tmp_path, str(file_path))
        tmp_path = None  # Prevent cleanup since file was moved
        logger.info("Updated %s", file_path)

    except Exception as e:
        logger.error("Error saving YAML file %s: %s", file_path, e)
        raise
    finally:
        if tmp_fd is not None:
            os.close(tmp_fd)
        if tmp_path is not None:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

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
            logger.info("%s: %s (%d models)", result.provider_name, result.status.value, result.model_count)
        else:
            logger.warning("%s: %s - %s", result.provider_name, result.status.value, result.error_message)
            stats.add_failed_provider(result.provider_name, result.error_message)

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
            seen_providers = set()

            # Update YAML with previously fetched models
            for provider_name, models in provider_models.items():
                is_stale, old_count, new_count = check_staleness(
                    provider_name, models, yaml_data
                )
                if is_stale:
                    logger.warning(
                        "Staleness detected for %s: %d -> %d models "
                        "(%.0f%% of previous, threshold %.0f%%)",
                        provider_name, old_count, new_count,
                        (new_count / old_count) * 100,
                        STALENESS_THRESHOLD * 100,
                    )
                    stats.add_stale_provider(provider_name, old_count, new_count)
                    continue

                if update_yaml_models(yaml_data, provider_name, models):
                    updates_made = True
                    if provider_name not in seen_providers:
                        stats.add_provider_result(provider_name, old_count, new_count)
                        seen_providers.add(provider_name)

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

    return stats

if __name__ == "__main__":
    import sys

    try:
        stats = main()
        success = stats is not None and len(stats.updated_files) > 0
        logger.info("Script completed with success=%s", success)
        exit(0 if success else 1)
    except Exception as e:
        logger.critical("Unexpected error occurred", exc_info=True)
        exit(1)
