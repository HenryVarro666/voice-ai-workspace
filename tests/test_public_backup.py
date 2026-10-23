"""Exercise public backups against temporary source trees and real bare remotes."""

from contextlib import redirect_stdout
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "backup_public.py"


def git(root, *args):
    result = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, check=True
    )
    return result.stdout.decode().strip()


class PublicBackupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        spec = importlib.util.spec_from_file_location("public_backup", SCRIPT)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)
        self.config = {
            "state_dir": "state",
            "allowlist": "allowlist.json",
            "repositories": [],
        }
        (self.root / "allowlist.json").write_text('{"findings": []}\n')
        self.config_path = self.root / "config.json"

    def repo(self, name="example"):
        source = self.root / (name + "-source")
        public = self.root / (name + "-public")
        remote = self.root / (name + ".git")
        source.mkdir()
        public.mkdir()
        git(public, "init", "-b", "main")
        git(public, "config", "user.name", "Backup Test")
        git(public, "config", "user.email", "backup@example.invalid")
        (public / "hello.py").write_text("ONE = 1\nTWO = 2\nTHREE = 3\n")
        (source / "hello.py").write_bytes((public / "hello.py").read_bytes())
        git(public, "add", ".")
        git(public, "commit", "-m", "public baseline")
        subprocess.run(
            ["git", "init", "--bare", str(remote)], check=True, capture_output=True
        )
        git(public, "remote", "add", "origin", str(remote))
        git(public, "push", "-u", "origin", "main")
        self.config["repositories"].append(
            {
                "name": name,
                "source": source.name,
                "public_checkout": public.name,
                "remote": str(remote),
                "branch": "main",
                "include": ["."],
                "preserve": [],
                "overrides": {},
                "approved_binary_paths": [],
            }
        )
        self.save_config()
        return source, public, remote

    def save_config(self):
        self.config_path.write_text(json.dumps(self.config))

    def tool(self):
        return self.module.Backup(self.config_path)

    def init(self):
        with redirect_stdout(io.StringIO()):
            self.tool().initialize()

    def preview(self):
        with redirect_stdout(io.StringIO()):
            return self.tool().preview()

    def push(self, plan):
        with redirect_stdout(io.StringIO()):
            self.tool().push(plan, confirmation="PUSH " + Path(plan).name)

    def remote_head(self, remote):
        return git(remote, "rev-parse", "refs/heads/main")

    def test_requires_explicit_initialization(self):
        self.repo()
        with self.assertRaisesRegex(self.module.BackupError, "init"):
            self.preview()

    def test_preview_leaves_original_and_public_heads_and_remote_unchanged(self):
        source, public, remote = self.repo()
        git(source, "init", "-b", "private-development")
        git(source, "config", "user.name", "Private Test")
        git(source, "config", "user.email", "private@example.invalid")
        (source / ".env").write_text("DO_NOT_PUBLISH=yes\n")
        git(source, "add", ".")
        git(source, "commit", "-m", "private source history")
        self.init()
        original = git(source, "rev-parse", "HEAD")
        public_head = self.remote_head(remote)
        (source / "hello.py").write_text("ONE = 7\nTWO = 2\nTHREE = 3\n")
        plan = self.preview()
        self.assertTrue((Path(plan) / "changes.md").is_file())
        self.assertEqual(git(source, "rev-parse", "HEAD"), original)
        self.assertEqual(git(public, "rev-parse", "HEAD"), public_head)
        self.assertEqual(self.remote_head(remote), public_head)
        self.assertIn("M\thello.py", (Path(plan) / "changes.md").read_text())

    def test_add_modify_delete_and_remote_only_files_survive(self):
        source, public, remote = self.repo()
        (source / "remove.py").write_text("REMOVE = True\n")
        (public / "remove.py").write_bytes((source / "remove.py").read_bytes())
        (public / "remote-only.md").write_text("Curated public text.\n")
        git(public, "add", ".")
        git(public, "commit", "-m", "curated files")
        git(public, "push")
        self.init()
        (source / "remove.py").unlink()
        (source / "added.py").write_text("ADDED = True\n")
        (source / "hello.py").write_text("ONE = 7\nTWO = 2\nTHREE = 3\n")
        plan = self.preview()
        self.push(plan)
        tree = git(remote, "ls-tree", "-r", "--name-only", "main")
        self.assertIn("remote-only.md", tree)
        self.assertIn("added.py", tree)
        self.assertNotIn("remove.py", tree)
        self.assertIn("ONE = 7", git(remote, "show", "main:hello.py"))
        again = json.loads((Path(self.preview()) / "plan.json").read_text())
        self.assertFalse(any(row["changed"] for row in again["repositories"]))

    def test_excludes_credentials_models_media_and_local_runtime(self):
        source, public, remote = self.repo()
        self.init()
        for name in [".env", ".envrc", "credentials.json", "credentials.yml", "auth.json", "movie.MP4", "voice.WAV", "model.bin",
                     "model.safetensors", "trace.log", "voice.wav.txt"]:
            (source / name).write_text("local-only\n")
        (source / "models").mkdir()
        (source / "models/config.json").write_text("{}")
        (source / "ok.py").write_text("OK = 1\n")
        plan = self.preview()
        self.push(plan)
        names = git(remote, "ls-tree", "-r", "--name-only", "main").splitlines()
        self.assertEqual(set(names), {"hello.py", "ok.py", "PUBLICATION_MANIFEST.json"})

    def test_symlink_and_embedded_audio_fail_closed(self):
        source, _, _ = self.repo()
        self.init()
        outside = self.root / "private.py"
        outside.write_text("PRIVATE = 1\n")
        (source / "link.py").symlink_to(outside)
        with self.assertRaisesRegex(self.module.BackupError, "symlink"):
            self.preview()
        (source / "link.py").unlink()
        (source / "player.html").write_text("data:audio/wav;base64," + "A" * 700)
        with self.assertRaisesRegex(self.module.BackupError, "embedded"):
            self.preview()

    def test_new_credential_is_blocked_without_exposing_value(self):
        source, _, remote = self.repo()
        self.init()
        token = "ghp_" + "Ab9X" * 10
        (source / "client.py").write_text("API_TOKEN = " + repr(token) + "\n")
        before = self.remote_head(remote)
        with self.assertRaises(self.module.BackupError) as error:
            self.preview()
        self.assertNotIn(token, str(error.exception))
        self.assertEqual(self.remote_head(remote), before)

    def test_local_changes_after_preview_invalidate_plan(self):
        source, _, remote = self.repo()
        self.init()
        (source / "added.py").write_text("ADDED = 1\n")
        plan = self.preview()
        before = self.remote_head(remote)
        (source / "added.py").write_text("ADDED = 2\n")
        with self.assertRaisesRegex(self.module.BackupError, "source.*changed"):
            self.push(plan)
        self.assertEqual(self.remote_head(remote), before)

    def test_refuses_wrong_confirmation_and_changed_policy(self):
        source, _, remote = self.repo()
        self.init()
        (source / "added.py").write_text("ADDED = 1\n")
        plan = self.preview()
        before = self.remote_head(remote)
        with self.assertRaisesRegex(self.module.BackupError, "confirmation"):
            self.tool().push(plan, confirmation="yes")
        (self.root / "allowlist.json").write_text('{"findings": [], "changed": true}')
        with self.assertRaisesRegex(self.module.BackupError, "policy.*changed"):
            self.push(plan)
        self.assertEqual(self.remote_head(remote), before)

    def test_remote_advancement_blocks_all_pushes_before_first_write(self):
        first_source, _, first_remote = self.repo("first")
        second_source, second_public, second_remote = self.repo("second")
        self.init()
        for source in [first_source, second_source]:
            (source / "added.py").write_text("ADDED = 1\n")
        plan = self.preview()
        before = self.remote_head(first_remote)
        other = self.root / "other-contributor"
        git(self.root, "clone", "--branch", "main", str(second_remote), str(other))
        git(other, "config", "user.name", "Other Contributor")
        git(other, "config", "user.email", "other@example.invalid")
        (other / "other.md").write_text("A different contributor's change.\n")
        git(other, "add", ".")
        git(other, "commit", "-m", "remote moved")
        git(other, "push")
        with self.assertRaisesRegex(self.module.BackupError, "remote.*changed"):
            self.push(plan)
        self.assertEqual(self.remote_head(first_remote), before)

    def test_deleted_media_in_new_remote_history_is_blocked(self):
        _, public, remote = self.repo()
        self.init()
        (public / "voice.wav").write_bytes(b"private waveform")
        git(public, "add", ".")
        git(public, "commit", "-m", "accidentally added media")
        git(public, "rm", "voice.wav")
        git(public, "commit", "-m", "deleted media from current tree")
        git(public, "push")
        before = self.remote_head(remote)
        with self.assertRaisesRegex(self.module.BackupError, "Forbidden"):
            self.preview()
        self.assertEqual(self.remote_head(remote), before)

    def test_embedded_media_in_remote_only_document_is_blocked(self):
        _, public, _ = self.repo()
        self.init()
        (public / "recording.html").write_text("data:audio/wav;base64," + "A" * 700)
        git(public, "add", ".")
        git(public, "commit", "-m", "remote embedded media")
        git(public, "push")
        with self.assertRaisesRegex(self.module.BackupError, "embedded"):
            self.preview()

    def test_nonoverlapping_remote_edit_merges_and_overlapping_edit_blocks(self):
        source, public, remote = self.repo()
        self.init()
        (public / "hello.py").write_text("ONE = 1\nTWO = 2\nTHREE = 9\n")
        git(public, "add", ".")
        git(public, "commit", "-m", "remote edit")
        git(public, "push")
        (source / "hello.py").write_text("ONE = 7\nTWO = 2\nTHREE = 3\n")
        plan = self.preview()
        self.push(plan)
        self.assertEqual(git(remote, "show", "main:hello.py"), "ONE = 7\nTWO = 2\nTHREE = 9")
        (public / "hello.py").write_text("ONE = 8\nTWO = 2\nTHREE = 9\n")
        git(public, "add", ".")
        git(public, "commit", "-m", "overlapping remote edit")
        git(public, "push")
        (source / "hello.py").write_text("ONE = 6\nTWO = 2\nTHREE = 3\n")
        with self.assertRaisesRegex(self.module.BackupError, "conflict"):
            self.preview()

    def test_original_source_history_is_never_pushed(self):
        source, _, remote = self.repo()
        git(source, "init", "-b", "private")
        git(source, "config", "user.name", "Private Test")
        git(source, "config", "user.email", "private@example.invalid")
        (source / "private.wav").write_bytes(b"private waveform")
        git(source, "add", ".")
        git(source, "commit", "-m", "private source history")
        private = git(source, "rev-parse", "HEAD")
        self.init()
        (source / "added.py").write_text("ADDED = 1\n")
        self.push(self.preview())
        all_commits = git(remote, "rev-list", "--all")
        self.assertNotIn(private, all_commits)
        objects = git(remote, "rev-list", "--objects", "--all")
        self.assertNotIn("private.wav", objects)

    def test_override_protects_private_coordination_log(self):
        source, _, remote = self.repo()
        (source / "PROJECT_STATUS.md").write_text("private operational log\n")
        (source / "public_docs").mkdir()
        (source / "public_docs/PROJECT_STATUS.md").write_text("public status\n")
        self.config["repositories"][0]["include"] = ["hello.py"]
        self.config["repositories"][0]["overrides"] = {
            "PROJECT_STATUS.md": "public_docs/PROJECT_STATUS.md"
        }
        self.save_config()
        self.init()
        self.push(self.preview())
        self.assertEqual(git(remote, "show", "main:PROJECT_STATUS.md"), "public status")

    def test_partial_push_can_resume_without_duplicate_commits(self):
        first_source, _, first_remote = self.repo("first")
        second_source, _, second_remote = self.repo("second")
        self.init()
        for source in [first_source, second_source]:
            (source / "added.py").write_text("ADDED = 1\n")
        plan = self.preview()
        hook = second_remote / "hooks/pre-receive"
        hook.write_text("#!/bin/sh\nexit 1\n")
        hook.chmod(0o755)
        with self.assertRaises(self.module.BackupError):
            self.push(plan)
        first = self.remote_head(first_remote)
        hook.unlink()
        self.push(plan)
        self.assertEqual(self.remote_head(first_remote), first)
        self.assertIn("added.py", git(second_remote, "ls-tree", "-r", "--name-only", "main"))

    def test_hub_pins_code_commits_and_second_run_is_unchanged(self):
        source, _, code_remote = self.repo("code")
        hub_source, hub_public, hub_remote = self.repo("voice-ai-workspace")
        pins = {"code_repositories": [{"name": "code", "commit": self.remote_head(code_remote)}]}
        (hub_public / "REPOSITORIES.json").write_text(json.dumps(pins))
        git(hub_public, "add", ".")
        git(hub_public, "commit", "-m", "initial code pin")
        git(hub_public, "push")
        self.config["repositories"][1]["preserve"] = ["REPOSITORIES.json"]
        self.save_config()
        self.init()
        (source / "added.py").write_text("ADDED = 1\n")
        self.push(self.preview())
        actual = json.loads(git(hub_remote, "show", "main:REPOSITORIES.json"))
        self.assertEqual(actual["code_repositories"][0]["commit"], self.remote_head(code_remote))
        self.assertIn(".public-backup/", git(hub_remote, "show", "main:.gitignore"))
        again = json.loads((self.preview() / "plan.json").read_text())
        self.assertFalse(any(row["changed"] for row in again["repositories"]))


if __name__ == "__main__":
    unittest.main()
