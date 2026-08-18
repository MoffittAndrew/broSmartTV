from app_logging import get_adapter

logger = get_adapter("git", "git")
logger.info("Importing git interface...")

import subprocess
from pathlib import Path

from globals import GIT, PATH


class GitInterface:
    def __init__(self, repo_path=None, branch_file_path=None, default_branch=None, command_runner=None, *args, **kwargs):
        self.__repo_path = Path(repo_path) if repo_path is not None else Path(PATH)
        self.__branch_file_path = Path(branch_file_path) if branch_file_path is not None else Path(GIT.BRANCH_FILE)
        self.__default_branch = default_branch or GIT.DEFAULT_BRANCH
        self.__command_runner = command_runner or subprocess.run
        self.__available_branches = []

    def _run_command(self, command, timeout=None):
        return self.__command_runner(
            command,
            cwd=self.__repo_path,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

    def _parse_branch_refs(self, output):
        branches = set()
        for line in output.splitlines():
            name = line.strip()
            if not name or name == "origin/HEAD":
                continue
            if name.startswith("origin/"):
                name = name[len("origin/"):]
            branches.add(name)
        return sorted(branches)

    def getCurrentBranch(self):
        # Intentionally read-only: unlike launcher/update's read_target_branch(), we never
        # create the branch file here, since this is just a display/refresh path.
        try:
            content = self.__branch_file_path.read_text(encoding="utf-8")
        except OSError:
            return self.__default_branch

        branch = content.strip()
        return branch or self.__default_branch

    def refreshAvailableBranches(self):
        logger.info("Refreshing available git branches...")

        fetch_result = self._run_command(["git", "fetch", "--prune", "origin"], timeout=15)
        if fetch_result.returncode != 0:
            error_text = (fetch_result.stderr or fetch_result.stdout or "").strip()
            logger.error("Failed to fetch git branches", error=error_text)
            raise RuntimeError(error_text or "Failed to fetch remote branches.")

        list_result = self._run_command(
            ["git", "for-each-ref", "--format=%(refname:short)", "refs/heads", "refs/remotes/origin"],
            timeout=15,
        )
        if list_result.returncode != 0:
            error_text = (list_result.stderr or list_result.stdout or "").strip()
            logger.error("Failed to list git branches", error=error_text)
            raise RuntimeError(error_text or "Failed to list git branches.")

        self.__available_branches = self._parse_branch_refs(list_result.stdout)
        logger.info("Available git branches refreshed", branch_count=len(self.__available_branches))
        return list(self.__available_branches)

    def getAvailableBranches(self):
        return list(self.__available_branches)

    def switchBranch(self, branch_name):
        branch_name = (branch_name or "").strip()
        if not branch_name:
            raise ValueError("A branch name is required.")

        if branch_name not in self.__available_branches:
            raise ValueError(f"Branch '{branch_name}' is not a known branch. Refresh the branch list and try again.")

        # Only edit the branch file; launcher/update applies the actual switch/pull on next restart.
        self.__branch_file_path.parent.mkdir(parents=True, exist_ok=True)
        self.__branch_file_path.write_text(branch_name + "\n", encoding="utf-8")
        logger.info("Git branch selection updated", branch=branch_name)
        return branch_name


gitInterface = GitInterface()
