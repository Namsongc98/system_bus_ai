#!/usr/bin/env python3

import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("claude_hook.py")
SPEC = importlib.util.spec_from_file_location("claude_hook", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class ClaudeHookSecretPolicyTest(unittest.TestCase):
    def setUp(self):
        self.root = Path("/workspace/System_bus")

    def reasons(self, command):
        return MODULE.blocked_command_reasons(command, self.root)

    def test_blocks_dotenv_file_access(self):
        commands = [
            "cat ticket-system/booking_ticket/.env",
            "sed -n '1,20p' booking_ticket_vue/.env.local",
            "rg JWT_SECRET ticket-system/.env.example",
            'python3 -c "from pathlib import Path; Path(\'.env\').read_text()"',
        ]

        for command in commands:
            with self.subTest(command=command):
                self.assertIn("dotenv_file_access", self.reasons(command))

    def test_blocks_environment_dump_commands(self):
        commands = [
            "env",
            "/usr/bin/env",
            "printenv JWT_SECRET",
            "command printenv DB_PASSWORD",
            "export -p",
            "declare -x",
        ]

        for command in commands:
            with self.subTest(command=command):
                self.assertIn("environment_dump", self.reasons(command))

    def test_blocks_sensitive_environment_references(self):
        commands = [
            'echo "$JWT_SECRET"',
            "printf '%s' ${DB_PASSWORD}",
            "JWT_SECRET=temporary mvn spring-boot:run",
            "MAIL_PASSWORD=value ./send-mail",
            "MINIO_SECRET_KEY=value ./upload",
        ]

        for command in commands:
            with self.subTest(command=command):
                self.assertIn(
                    "sensitive_environment_reference",
                    self.reasons(command),
                )

    def test_allows_sanitized_configuration_inspection(self):
        commands = [
            "mvn -f ticket-system/pom.xml test -DskipTests",
            "rg DB_PASSWORD .claude/references/backend/environment-variable-names.md",
            "sed -n '1,120p' ticket-system/manage-revenue-ticket/src/main/resources/application.properties",
        ]

        for command in commands:
            with self.subTest(command=command):
                self.assertEqual([], self.reasons(command))

    def test_scan_open_ledger_items_ignores_readme_and_template(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ledger_dir = root / ".claude" / "ledger"
            ledger_dir.mkdir(parents=True)
            (ledger_dir / "README.md").write_text("- [ ] not a real item\n")
            (ledger_dir / "TEMPLATE.md").write_text("- [ ] not a real item\n")
            (ledger_dir / "demo-feature.md").write_text(
                "## admin/trip\n- [x] spec\n- [ ] implement\n"
            )

            findings = MODULE.scan_open_ledger_items(root)

        self.assertEqual(len(findings), 1)
        self.assertIn("demo-feature.md", findings[0]["ledger"])
        self.assertEqual(findings[0]["open_items"], 1)


class ClaudeHookCliTest(unittest.TestCase):
    """Run the script the way Claude Code does: exit code plus stdout/stderr."""

    def run_hook(self, event, *extra, payload=""):
        import subprocess
        import sys
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            return subprocess.run(
                [sys.executable, str(SCRIPT), "--event", event, *extra],
                input=payload,
                capture_output=True,
                text=True,
                cwd=tmp,
                check=False,
            )

    def test_blocked_command_reason_goes_to_stderr(self):
        result = self.run_hook("PreToolUse", "--dry-run-command", "git push --force origin main")

        self.assertEqual(result.returncode, 2)
        self.assertIn("force_push", result.stderr)
        self.assertEqual(result.stdout, "")

    def test_clean_prompt_adds_no_context(self):
        result = self.run_hook("UserPromptSubmit", "--dry-run-prompt", "review the booking flow")

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_stop_blocks_on_secret_in_diff(self):
        # Built at runtime so this file does not itself trip the secret scan.
        diff = "+++ b/src/main/resources/application.yml\n+jwt." + "secret: " + "abcdefgh" * 2 + "\n"
        result = self.run_hook("Stop", "--dry-run-diff", diff, "--dry-run-changed", "")

        self.assertEqual(result.returncode, 2)
        self.assertIn("secret", result.stderr)

    def test_stop_blocks_once_on_uncommitted_code_changes(self):
        changed = "ticket-system/booking_ticket/src/Foo.java,booking_ticket_vue/README.md"
        first = self.run_hook("Stop", "--dry-run-diff", "", "--dry-run-changed", changed)
        again = self.run_hook(
            "Stop", "--dry-run-diff", "", "--dry-run-changed", changed,
            payload='{"stop_hook_active": true}',
        )

        self.assertEqual(first.returncode, 2)
        self.assertIn("Foo.java", first.stderr)
        self.assertNotIn("README.md", first.stderr)
        self.assertEqual(again.returncode, 0)

    def test_stop_allows_docs_only_changes(self):
        result = self.run_hook("Stop", "--dry-run-diff", "", "--dry-run-changed", ".claude/docs/report/x.md")

        self.assertEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
