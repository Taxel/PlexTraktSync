from plextraktsync.decorators.deprecated import deprecated


@deprecated("Use version() instead")
def release_version():
    from plextraktsync import __version__

    if __version__[-1] != 'x':
        return __version__

    return None


@deprecated("Use version() instead")
def git_version_info():
    try:
        from gitinfo import get_git_info
    except (ImportError, TypeError):
        return release_version()

    commit = get_git_info()
    if not commit:
        return release_version()

    message = commit['message'].split("\n")[0]

    return f"{commit['commit'][0:8]}: {message} @{commit['author_date']}"


def version():
    v = release_version()
    if v:
        return v

    from plextraktsync import __version__
    gv = git_version_info()
    if gv:
        return f"{__version__}: {gv}"

    return __version__
