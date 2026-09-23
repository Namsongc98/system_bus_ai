#!/usr/bin/env python3

import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("codex_hook.py")
SPEC = importlib.util.spec_from_file_location("claude_codex_hook", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class CodexHookSecretPolicyTest(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
