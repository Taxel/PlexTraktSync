def git_version_info():
    try:
        from gitinfo import get_git_info
    except (ImportError, TypeError):
        return None

    commit = get_git_info()
    if not commit:
        return None

    return f"{commit['commit'][0:8]}: {commit['message']} @{commit['author_date']}"
