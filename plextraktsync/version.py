from plextraktsync.decorators.cached_property import cached_property


class Version:
    @cached_property
    def version(self):
        from plextraktsync import __version__

        # Released in PyPI
        if not __version__.endswith(".0dev0"):
            return __version__

        gv = git_version_info()
        if gv:
            return f"{__version__}: {gv}"

        return __version__


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
