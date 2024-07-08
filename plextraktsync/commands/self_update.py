from __future__ import annotations

from plextraktsync.factory import factory
from plextraktsync.util.execp import execp


def has_previous_pr(pr: int):
    from plextraktsync.util.packaging import pipx_installed

    package = pipx_installed(f"plextraktsync@{pr}")

    return package is not None


def pr_number() -> int | None:
    """
    Check if current executable is named plextraktsync@<pr>
    """

    import sys

    try:
        pr = sys.argv[0].split("@")[1]
    except IndexError:
        return None

    if pr.isnumeric():
        return int(pr)
    return None


def self_update(pr: int):
    print = factory.print

    if not pr:
        pr = pr_number()
        if pr:
            print(f"Installed as pr #{pr}, enabling pr mode")

    if pr:
        if has_previous_pr(pr):
            # Uninstall because pipx doesn't update otherwise:
            # - https://github.com/pypa/pipx/issues/902
            print(f"Uninstalling previous plextraktsync@{pr}")
            execp(f"pipx uninstall plextraktsync@{pr}")

        print(f"Updating PlexTraktSync to the pull request #{pr} version using pipx")
        execp(f"pipx install --suffix=@{pr} --force git+https://github.com/Taxel/PlexTraktSync@refs/pull/{pr}/head")
        return

    print("Updating PlexTraktSync to the latest version using pipx")
    execp("pipx upgrade PlexTraktSync")
