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
