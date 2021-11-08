def git_version_info():
    try:
        from gitinfo import get_git_info
    except (ImportError, TypeError):
        return None

    commit = get_git_info()
    if not commit:
        return None

    message = commit['message'].split("\n")[0]

    return f"{commit['commit'][0:8]}: {message} @{commit['author_date']}"


def version():
    from plextraktsync import __version__

    if __version__[-1] != 'x':
        return __version__

    gv = git_version_info()
    if gv:
        return f"{__version__}: {gv}"

    return __version__
