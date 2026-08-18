import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "py" / "interface"))

import git_interface


class FakeCompletedProcess:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


class RecordingCommandRunner:
    def __init__(self, results):
        # results: dict keyed by the joined command string -> FakeCompletedProcess
        self.results = results
        self.commands = []

    def __call__(self, command, **kwargs):
        self.commands.append(command)
        key = " ".join(command)
        for pattern, result in self.results.items():
            if pattern in key:
                return result
        return FakeCompletedProcess()


def make_interface(tmp_path, command_runner=None):
    branch_file_path = tmp_path / "launcher" / "branch"
    return git_interface.GitInterface(
        repo_path=tmp_path,
        branch_file_path=branch_file_path,
        command_runner=command_runner or (lambda *args, **kwargs: FakeCompletedProcess()),
    )


def test_get_current_branch_defaults_when_file_missing(tmp_path):
    interface = make_interface(tmp_path)
    assert interface.getCurrentBranch() == "live"


def test_get_current_branch_trims_whitespace(tmp_path):
    interface = make_interface(tmp_path)
    branch_file_path = tmp_path / "launcher" / "branch"
    branch_file_path.parent.mkdir(parents=True, exist_ok=True)
    branch_file_path.write_text("  dev  \n", encoding="utf-8")

    assert interface.getCurrentBranch() == "dev"


def test_get_current_branch_does_not_create_file(tmp_path):
    interface = make_interface(tmp_path)
    interface.getCurrentBranch()

    assert not (tmp_path / "launcher" / "branch").exists()


def test_refresh_available_branches_parses_and_dedupes(tmp_path):
    runner = RecordingCommandRunner({
        "git fetch": FakeCompletedProcess(returncode=0),
        "for-each-ref": FakeCompletedProcess(
            returncode=0,
            stdout="origin/live\norigin/dev\norigin/feature-x\norigin/HEAD\n",
        ),
    })
    interface = make_interface(tmp_path, command_runner=runner)

    branches = interface.refreshAvailableBranches()

    assert branches == ["dev", "feature-x", "live"]
    assert interface.getAvailableBranches() == ["dev", "feature-x", "live"]


def test_refresh_available_branches_excludes_stale_local_only_branches(tmp_path):
    # A branch once checked out on the Pi but since deleted from GitHub should not appear,
    # since only refs/remotes/origin (what's actually pullable) is queried.
    runner = RecordingCommandRunner({
        "git fetch": FakeCompletedProcess(returncode=0),
        "for-each-ref": FakeCompletedProcess(returncode=0, stdout="origin/live\n"),
    })
    interface = make_interface(tmp_path, command_runner=runner)

    branches = interface.refreshAvailableBranches()

    assert branches == ["live"]
    assert not any("refs/heads" in command for command in runner.commands)


def test_refresh_available_branches_raises_on_fetch_failure(tmp_path):
    runner = RecordingCommandRunner({
        "git fetch": FakeCompletedProcess(returncode=1, stderr="network unreachable"),
    })
    interface = make_interface(tmp_path, command_runner=runner)

    with pytest.raises(RuntimeError, match="network unreachable"):
        interface.refreshAvailableBranches()


def test_switch_branch_rejects_unknown_branch(tmp_path):
    interface = make_interface(tmp_path)

    with pytest.raises(ValueError, match="not a known branch"):
        interface.switchBranch("nonexistent")


def test_switch_branch_writes_file_and_never_checks_out(tmp_path):
    runner = RecordingCommandRunner({
        "git fetch": FakeCompletedProcess(returncode=0),
        "for-each-ref": FakeCompletedProcess(returncode=0, stdout="live\ndev\n"),
    })
    interface = make_interface(tmp_path, command_runner=runner)
    interface.refreshAvailableBranches()

    result = interface.switchBranch("dev")

    branch_file_path = tmp_path / "launcher" / "branch"
    assert result == "dev"
    assert branch_file_path.read_text(encoding="utf-8") == "dev\n"
    assert not any(
        "checkout" in command or "switch" in command or "pull" in command
        for command in runner.commands
    )
