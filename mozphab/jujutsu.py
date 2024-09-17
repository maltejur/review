import os
import re
from pathlib import Path

from .exceptions import Error
from .git import Git
from .logger import logger
from .repository import Repository
from .subprocess_wrapper import check_output


class Jujutsu(Repository):
    @classmethod
    def is_repo(cls, path: str) -> bool:
        """Quick check for repository at specified path."""
        return os.path.exists(os.path.join(path, ".jj"))

    # ----
    # Methods expected from callers of the `Repository` interface:
    # ----

    def __init__(self, path: str):
        # NOTE: We expect a co-located Git repository alongside the Jujutsu repository, so let's
        # start up a Git backend to handle the pieces we need.

        # Since there could be multiple Jujutsu workspaces, and the underlying
        # Git repository could be in either one of them, or in another folder
        # entirely, we will need to do a small search first.

        self.git_path = Path(path)
        repo = self.git_path / ".jj" / "repo"
        if repo.is_file():
            # NOTE: This should point to the root of the repository, with the `.jj` directory right
            # inside.
            self.git_path = Path(repo.read_text()).parent.parent
        git_target = self.git_path / ".jj" / "repo" / "store" / "git_target"
        if git_target.is_file():
            store_dir_path = git_target.parent
            git_repo_dir_path = Path(git_target.read_text())
            ugly_git_dir_path = store_dir_path.joinpath(git_repo_dir_path)
            ugly_git_repo_path = (
                ugly_git_dir_path.parent
            )  # slice off the `.git` segment
            pretty_git_repo_path = ugly_git_repo_path.resolve()
            self.git_path = pretty_git_repo_path
        logger.debug(f"git_path: {self.git_path}")

        if (self.git_path / ".git").is_dir():
            self.__git_repo = Git(self.git_path)
        else:
            # TODO: Do we actually only support co-located Git repos now? 🤔
            raise Error(
                "Underlying Git repository for Jujutsu could not be found. "
                "Make sure you are using a colocated Git repository and not "
                "the pure Jujutsu backend."
            )

        # Populate common fields expected from a `Repository`

        dot_path = os.path.join(path, ".jj")
        if not os.path.exists(dot_path):
            raise ValueError("%s: not a Jujutsu repository" % path)
        logger.debug("found Jujutsu repo in %s", path)
        super().__init__(path, dot_path)

        self.vcs = "jj"

        version_output = check_output(["jj", "--version"], split=False)
        m = re.search(r"jj (\d+\.\d+\.\d+.*)", version_output)
        if not m:
            raise Error("Failed to determine Jujutsu version.")
        self.vcs_version = m.group(0)

        self.revset = None
        self.branch = None
