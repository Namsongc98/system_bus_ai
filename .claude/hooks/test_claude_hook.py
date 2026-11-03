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

    def test_blocks_dotenv_globs_and_environment_readers(self):
        commands = {
            "find . -name '.env*' -exec cat {} +": "dotenv_file_access",
            "cat .e*": "dotenv_file_access",
            "cat /proc/self/environ": "environment_dump",
            "set": "environment_dump",
            "python3 -c 'import os;print(os.environ)'": "environment_dump",
            "node -e 'console.log(process.env)'": "environment_dump",
        }

        for command, reason in commands.items():
            with self.subTest(command=command):
                self.assertIn(reason, self.reasons(command))

    def test_blocks_bash_writes_to_guard_and_secret_files(self):
        commands = [
            "echo x > .claude/settings.json",
            "echo x >> .claude/hooks/claude_hook.py",
            "tee .claude/settings.local.json",
            "sed -i '' s/a/b/ .claude/hooks/claude_hook.py",
            "cp /tmp/x .claude/hooks/claude_hook.py",
            "ls; mv .claude/settings.json /tmp/s",
            "git checkout -- .claude/hooks/claude_hook.py",
            "git diff --output=.claude/settings.json",
            "python3 -c \"open('.claude/settings.json','w').write('{}')\"",
        ]

        for command in commands:
            with self.subTest(command=command):
                self.assertIn("protected_path_write", self.reasons(command))

    def test_allows_main_session_reads_and_repo_writes(self):
        commands = [
            "sed -n 1,20p .claude/hooks/claude_hook.py",
            "python3 .claude/hooks/claude_hook.py --event PreToolUse --dry-run-command 'echo x > out.txt'",
            "git add -- .claude/hooks/claude_hook.py",
            "git -C ticket-system commit -F - <<'EOF'\nmessage with a user's quote\nEOF",
            "cat >> CLAUDE.md <<'EOF'\nsee .claude/hooks/claude_hook.py > it's fine\nEOF",
            "echo x > out.txt",
            "grep -rn 'process.env' booking_ticket_vue/src",
        ]

        for command in commands:
            with self.subTest(command=command):
                self.assertEqual([], self.reasons(command))

    def test_read_only_agents_get_an_allowlist(self):
        blocked = [
            "echo x > out.txt", "echo x | tee out.txt", "sed -i '' s/a/b/ f.txt",
            "git diff --output=o.txt", "git checkout -- .", "git commit -am x", "git stash",
            "git stash pop", "git branch new-branch", "git remote add x y", "git worktree add ../w",
            "curl http://x", "docker ps", "mvn clean install", "npm install",
            "find . -exec rm {} +", "cat x $(rm f)", "cat a\nrm b", "python3 -c 'print(1)'",
        ]
        allowed = [
            "git -C ticket-system diff -- f", "git grep -o foo", "grep -rn foo .claude",
            "sed -n 1,20p f", "find . -name '*.java'", "cat f | head -5", "ls 2>/dev/null",
            "git stash list", "git branch --show-current", "git remote get-url origin", "git worktree list",
            "mvn -B -f ticket-system/pom.xml -pl manage-revenue-ticket -am "
            "-Dtest=AvatarServiceTest#upload -Dsurefire.failIfNoSpecifiedTests=false test",
            "npm --prefix booking_ticket_vue run test:unit -- --run src/x.spec.js",
        ]

        for command in blocked:
            with self.subTest(blocked=command):
                self.assertNotEqual([], MODULE.read_only_agent_reasons(command, self.root))
        for command in allowed:
            with self.subTest(allowed=command):
                self.assertEqual([], MODULE.read_only_agent_reasons(command, self.root))

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

    def test_read_only_layer_applies_only_to_read_only_subagents(self):
        import json

        def payload(agent_type):
            data = {"tool_name": "Bash", "tool_input": {"command": "git commit -am x"}}
            if agent_type:
                data["agent_type"] = agent_type
            return json.dumps(data)

        main = self.run_hook("PreToolUse", payload=payload(None))
        verifier = self.run_hook("PreToolUse", payload=payload("finding-verifier"))
        plugin_reviewer = self.run_hook("PreToolUse", payload=payload("system-bus-dev:backend-reviewer"))
        general = self.run_hook("PreToolUse", payload=payload("general-purpose"))

        self.assertEqual(main.returncode, 0)
        self.assertEqual(verifier.returncode, 2)
        self.assertIn("read_only_agent_git_write:commit", verifier.stderr)
        self.assertEqual(plugin_reviewer.returncode, 2)
        self.assertEqual(general.returncode, 0)

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
