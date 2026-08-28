import argparse
import os
import subprocess
import sys
from pathlib import Path

from package_plugin import INSTALL_RUNTIME_FORBIDDEN_FILES, INSTALL_RUNTIME_REQUIRED_FILES, PackageError, PluginPackager


COMMAND_FILES = [
    "commands/spl.md",
    "commands/spl/prd.md",
    "commands/spl/ui.md",
    "commands/spl/design.md",
    "commands/spl/run.md",
    "commands/spl/status.md",
    "commands/spl/resume.md",
    "commands/spl/doctor.md",
]
FORBIDDEN_COMMAND_FILE = "commands/spl/manifest.md"
REQUIRED_RELEASE_INCLUDE = ".claude-plugin/plugin.json"
REQUIRED_SCHEMA_FILES = [
    "schemas/artifact-manifest.schema.json",
    "schemas/execution-manifest.schema.json",
    "schemas/interaction-flow.schema.json",
    "schemas/module-split.schema.json",
    "schemas/session-state.schema.json",
]
REQUIRED_AGENT_FILES = [
    "agents/analyst.md",
    "agents/ui-architect.md",
    "agents/architect.md",
    "agents/developer.md",
    "agents/code-reviewer.md",
    "agents/system_merger.md",
    "agents/tester.md",
    "agents/workspace_applier.md",
    "agents/requirement-verifier.md",
    "agents/impact-analyzer.md",
]
REQUIRED_RELEASE_EXCLUDE = [
    ".superlooper/runtime.txt",
    ".claude/CLAUDE.md",
    ".learnings/note.md",
    "docs/superpowers/demo.md",
    "docs/design/demo.md",
    "dist/demo.zip",
    "scripts/__pycache__/cached.pyc",
    "nested/__pycache__/cached.pyc",
    ".env",
    ".env.local",
    "tests/test_demo.py",
]


class DoctorError(Exception):
    pass


class DoctorRunner:
    def __init__(self, workspace_root, session_id=None, plugin_root=None):
        self.workspace_root = Path(workspace_root).resolve()
        self.plugin_root = Path(plugin_root).resolve() if plugin_root else Path(__file__).resolve().parents[1]
        self.session_id = session_id
        self.packager = PluginPackager(root=self.plugin_root, mode="install")
        self.results = []

    def run(self):
        self._run_check("plugin_validate", self.check_plugin_validate)
        self._run_check("python_compile", self.check_python_compile)
        self._run_check("commands_contract", self.check_commands_contract)
        self._run_check("schema_contract", self.check_schema_contract)
        self._run_check("agent_contract", self.check_agent_contract)
        self._run_check("forbidden_manifest_command", self.check_forbidden_manifest_command)
        self._run_check("release_filter", self.check_release_filter)
        self._run_check("session_contract", self.check_session_contract)
        for check_name, status, message in self.results:
            self._print_line(f"{check_name}: {status} - {message}")
        return 1 if any(status == "FAIL" for _, status, _ in self.results) else 0

    def _run_check(self, check_name, func):
        try:
            status, message = func()
        except Exception as exc:
            status, message = "FAIL", str(exc)
        self.results.append((check_name, status, self._single_line(message)))

    def check_plugin_validate(self):
        command = [*self.packager._claude_command_prefix(), "plugin", "validate", ".", "--strict"]
        completed = self._run_command(command)
        if completed.returncode != 0:
            return "FAIL", completed.stderr or completed.stdout or "claude plugin validate failed"
        return "PASS", "claude plugin validate . --strict"

    def check_python_compile(self):
        scripts = sorted(path for path in (self.plugin_root / "scripts").glob("*.py") if path.is_file())
        if not scripts:
            return "FAIL", "scripts 目录下没有可编译的 Python 文件"
        command = [sys.executable, "-m", "py_compile", *[str(path) for path in scripts]]
        completed = self._run_command(command)
        if completed.returncode != 0:
            return "FAIL", completed.stderr or completed.stdout or "py_compile failed"
        return "PASS", f"compiled {len(scripts)} scripts"

    def check_commands_contract(self):
        missing = [relative for relative in COMMAND_FILES if not (self.plugin_root / relative).exists()]
        if missing:
            return "FAIL", "missing: " + ", ".join(missing)
        return "PASS", f"found {len(COMMAND_FILES)} command files"

    def check_schema_contract(self):
        missing = [relative for relative in REQUIRED_SCHEMA_FILES if not (self.plugin_root / relative).exists()]
        if missing:
            return "FAIL", "missing: " + ", ".join(missing)
        return "PASS", f"found {len(REQUIRED_SCHEMA_FILES)} schema files"

    def check_agent_contract(self):
        missing = [relative for relative in REQUIRED_AGENT_FILES if not (self.plugin_root / relative).exists()]
        if missing:
            return "FAIL", "missing: " + ", ".join(missing)
        return "PASS", f"found {len(REQUIRED_AGENT_FILES)} agent files"

    def check_forbidden_manifest_command(self):
        path = self.plugin_root / FORBIDDEN_COMMAND_FILE
        if path.exists():
            return "FAIL", f"forbidden file exists: {FORBIDDEN_COMMAND_FILE}"
        return "PASS", "commands/spl/manifest.md is absent"

    def check_release_filter(self):
        release_files = set(self.packager._build_release_file_list())
        missing = sorted(INSTALL_RUNTIME_REQUIRED_FILES.difference(release_files))
        if missing:
            return "FAIL", "missing required release files: " + ", ".join(missing)
        forbidden = sorted(INSTALL_RUNTIME_FORBIDDEN_FILES.intersection(release_files))
        if forbidden:
            return "FAIL", "release files unexpectedly include: " + ", ".join(forbidden)
        for relative in REQUIRED_RELEASE_EXCLUDE:
            if not self.packager._should_skip_release_path(relative) or relative in release_files:
                return "FAIL", f"release filter unexpectedly keeps: {relative}"
        self.packager._scan_secrets(release_files)
        return "PASS", "install release filter keeps runtime closure, excludes blocked paths, and scans secrets"

    def check_session_contract(self):
        if not self.session_id:
            return "SKIPPED", "session_id not provided"
        command = [
            sys.executable,
            str(self.plugin_root / "scripts" / "validate_miao_contracts.py"),
            "--workspace-root",
            str(self.workspace_root),
            "--session-id",
            self.session_id,
            "--scope",
            "all",
        ]
        completed = self._run_command(command)
        if completed.returncode != 0:
            return "FAIL", completed.stderr or completed.stdout or "session contract validation failed"
        return "PASS", f"validated session {self.session_id}"

    def _run_command(self, command):
        return subprocess.run(
            command,
            cwd=self.plugin_root,
            text=True,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )

    def _single_line(self, message):
        return " ".join(str(message).split()) if message else "ok"

    def _print_line(self, text):
        encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
        sys.stdout.write(text.encode(encoding, errors="replace").decode(encoding, errors="replace") + "\n")
        sys.stdout.flush()


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Run SUPERLOOPER doctor checks.")
    parser.add_argument("--workspace-root", default=os.getenv("SUPERLOOPER_WORKSPACE_ROOT", os.getcwd()), help="目标项目根目录，默认使用 SUPERLOOPER_WORKSPACE_ROOT 或当前目录。")
    parser.add_argument("--plugin-root", default=os.getenv("SUPERLOOPER_PLUGIN_ROOT"), help="插件源码或安装根目录，默认使用当前脚本所在插件根。")
    parser.add_argument("--session-id", help="执行会话 ID。")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    try:
        runner = DoctorRunner(workspace_root=args.workspace_root, session_id=args.session_id, plugin_root=args.plugin_root)
        return runner.run()
    except (DoctorError, PackageError, ValueError) as exc:
        print(f"doctor failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
