def release_version():
    from plex_trakt_sync import __version__

    if __version__[:-1] != 'x':
        return __version__

    return None


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
