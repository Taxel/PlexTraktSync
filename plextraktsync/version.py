from plextraktsync.decorators.cached_property import cached_property


class Version:
    @cached_property
    def version(self):
        from plextraktsync import __version__

        # Released in PyPI
        if not __version__.endswith(".0dev0"):
            return __version__

        # Print version from pip
        if self.pipx_installed:
            v = self.vcs_info
            return f'{__version__[0:-4]}@pr/{v["pr"]}#{v["short_commit_id"]}'

        # If installed with Git
        gv = git_version_info()
        if gv:
            return f"{__version__}: {gv}"

        return __version__

    @property
    def vcs_info(self):
        from plextraktsync.util.packaging import vcs_info

        return vcs_info("PlexTraktSync")

    @property
    def pipx_installed(self):
        if not self.installed:
            return False

        from plextraktsync.util.packaging import pipx_installed, program_name

        package = pipx_installed(program_name())

        return package is not None

    @property
    def installed(self):
        from plextraktsync.util.packaging import installed

        return installed()


def git_version_info():
    try:
        from gitinfo import get_git_info
    except (ImportError, TypeError):
        return None

    commit = get_git_info()
    if not commit:
        return None

    message = commit["message"].split("\n")[0]

    return f"{commit['commit'][0:8]}: {message} @{commit['author_date']}"


VERSION = Version()


def version():
    return VERSION.version
