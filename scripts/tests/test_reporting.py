"""Tests for UpdateStats delta tracking, summary generation, and commit message formatting."""

import logging
import re

from update_models import UpdateStats


class TestUpdateStatsDeltas:
    """Tests for per-provider delta tracking in UpdateStats."""

    def test_add_provider_result_stores_old_and_new_count(self):
        stats = UpdateStats()
        stats.add_provider_result("OpenRouter", 50, 53)
        assert stats.provider_results == {"OpenRouter": (50, 53)}

    def test_add_failed_provider_stores_error_message(self):
        stats = UpdateStats()
        stats.add_failed_provider("Groq", "auth_error: invalid key")
        assert stats.failed_providers == {"Groq": "auth_error: invalid key"}

    def test_add_failed_provider_defaults_unknown_error(self):
        stats = UpdateStats()
        stats.add_failed_provider("Groq", None)
        assert stats.failed_providers == {"Groq": "unknown error"}

    def test_add_stale_provider(self):
        stats = UpdateStats()
        stats.add_stale_provider("Nvidia", 100, 10)
        assert stats.stale_providers == [("Nvidia", 100, 10)]

    def test_add_file_result_success(self):
        stats = UpdateStats()
        stats.add_file_result("f.yaml", True)
        assert stats.updated_files == ["f.yaml"]

    def test_add_file_result_failure(self):
        stats = UpdateStats()
        stats.add_file_result("f.yaml", False)
        assert stats.failed_files == ["f.yaml"]


class TestPrintSummary:
    """Tests for delta-aware print_summary output."""

    def test_successful_providers_shown_with_deltas(self, caplog):
        stats = UpdateStats()
        stats.add_provider_result("OpenRouter", 50, 53)
        with caplog.at_level(logging.INFO):
            stats.print_summary()
        assert "[OK] OpenRouter: 53 models (+3)" in caplog.text

    def test_failed_providers_shown_with_reason(self, caplog):
        stats = UpdateStats()
        stats.add_failed_provider("Groq", "auth_error: invalid key")
        with caplog.at_level(logging.INFO):
            stats.print_summary()
        assert "[FAIL] Groq: auth_error: invalid key" in caplog.text

    def test_stale_shown(self, caplog):
        stats = UpdateStats()
        stats.add_stale_provider("Nvidia", 100, 10)
        with caplog.at_level(logging.INFO):
            stats.print_summary()
        assert "[SKIP] Nvidia: 100 -> 10 models" in caplog.text

    def test_deltas_shown_negative(self, caplog):
        stats = UpdateStats()
        stats.add_provider_result("xAI", 20, 18)
        with caplog.at_level(logging.INFO):
            stats.print_summary()
        assert "[OK] xAI: 18 models (-2)" in caplog.text


class TestCommitMessage:
    """Tests for generate_commit_message output."""

    def test_subject_with_positive_delta(self):
        stats = UpdateStats()
        stats.add_provider_result("OpenRouter", 50, 53)
        msg = stats.generate_commit_message()
        subject = msg.split("\n")[0]
        assert "OpenRouter +3" in subject

    def test_subject_with_negative_delta(self):
        stats = UpdateStats()
        stats.add_provider_result("Groq", 10, 8)
        msg = stats.generate_commit_message()
        subject = msg.split("\n")[0]
        assert "Groq -2" in subject

    def test_subject_skips_zero_delta(self):
        stats = UpdateStats()
        stats.add_provider_result("Nvidia", 50, 50)
        msg = stats.generate_commit_message()
        subject = msg.split("\n")[0]
        assert "Nvidia" not in subject

    def test_subject_truncation_when_too_long(self):
        stats = UpdateStats()
        # Add many providers with deltas to exceed 72 chars
        for i in range(12):
            stats.add_provider_result("Provider%d" % i, 10, 10 + i + 1)
        msg = stats.generate_commit_message()
        subject = msg.split("\n")[0]
        assert len(subject) <= 72
        assert "providers" in subject

    def test_fallback_no_deltas(self):
        stats = UpdateStats()
        stats.add_provider_result("Nvidia", 50, 50)
        stats.add_provider_result("OpenRouter", 30, 30)
        msg = stats.generate_commit_message()
        subject = msg.split("\n")[0]
        assert re.match(r"chore: update models \(\d{4}-\d{2}-\d{2}\)", subject)

    def test_body_includes_provider_details(self):
        stats = UpdateStats()
        stats.add_provider_result("OpenRouter", 50, 53)
        msg = stats.generate_commit_message()
        assert "OpenRouter: 50 -> 53 (+3)" in msg

    def test_body_includes_failed_providers(self):
        stats = UpdateStats()
        stats.add_failed_provider("Groq", "auth_error")
        msg = stats.generate_commit_message()
        assert "Failed:" in msg
        assert "Groq: auth_error" in msg

    def test_body_includes_stale_providers(self):
        stats = UpdateStats()
        stats.add_stale_provider("Nvidia", 100, 10)
        msg = stats.generate_commit_message()
        assert "Stale (skipped):" in msg
        assert "Nvidia: 100 -> 10" in msg

    def test_full_message_has_subject_and_body(self):
        stats = UpdateStats()
        stats.add_provider_result("OpenRouter", 50, 53)
        msg = stats.generate_commit_message()
        parts = msg.split("\n\n", 1)
        assert len(parts) == 2
        assert parts[0]  # subject
        assert parts[1]  # body


class TestCommitFile:
    """Tests for .commit_msg file writing."""

    def test_commit_message_written_to_file(self, tmp_path):
        stats = UpdateStats()
        stats.add_provider_result("OpenRouter", 50, 53)
        msg_path = tmp_path / ".commit_msg"
        msg_path.write_text(stats.generate_commit_message(), encoding="utf-8")
        assert msg_path.exists()
        content = msg_path.read_text(encoding="utf-8")
        assert "chore: update models" in content
