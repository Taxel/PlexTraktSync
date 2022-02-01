from functools import cached_property


class Version:
    @property
    def version(self):
        from plextraktsync import __version__

        return __version__

    @cached_property
    def full_version(self):
        from plextraktsync import __version__

        # Released in PyPI
        if not __version__.endswith(".0dev0"):
            return __version__

        # Print version from pip
        if self.pipx_installed:
            v = self.vcs_info
            return f'{__version__[0:-4]}@pr/{v["pr"]}#{v["short_commit_id"]}'

        # If installed with Git
        gv = self.git_version_info
        if gv:
            return f"{__version__}: {gv}"

        return __version__

    @property
    def py_full_version(self):
        from sys import version

        return version.replace("\n", "")

    @property
    def py_version(self):
        from platform import python_version

        return python_version()

    @property
    def py_platform(self):
        from platform import platform

        return platform(terse=True, aliased=True)

    @property
    def plex_api_version(self):
        from plexapi import VERSION

        return VERSION

    @property
    def trakt_api_version(self):
        from trakt import __version__

        return __version__

    @property
    def git_version_info(self):
        from plextraktsync.util.git_version_info import git_version_info

        return git_version_info()

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
