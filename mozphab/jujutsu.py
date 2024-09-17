class Jujutsu(Repository):
    def __init__(self, path: str):
        # NOTE: We expect a co-located Git repository alongside the Jujutsu repository, so let's
        # start up a Git backend to handle the pieces we need.
        self.__git_repo = Git(path)

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
