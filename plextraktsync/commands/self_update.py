from os import system
from typing import Optional

import click


def enable_self_update():
    from plextraktsync.util.packaging import pipx_installed

    package = pipx_installed("plextraktsync")

    return package is not None


def has_previous_pr(pr: int):
    try:
        from plextraktsync.util.execx import execx
        execx(f"plextraktsync@{pr} --help")
    except FileNotFoundError:
        return False

    return True


def pr_number() -> Optional[int]:
    """
    Check if current executable is named plextraktsync@<pr>
    """

    import sys
    try:
        pr = sys.argv[0].split('@')[1]
    except IndexError:
        return None

    if pr.isnumeric():
        return int(pr)
    return None


def self_update(pr: int):
    if pr:
        if has_previous_pr(pr):
            # Uninstall because pipx doesn't update otherwise:
            # - https://github.com/pypa/pipx/issues/902
            click.echo(f"Uninstalling previous plextraktsync@{pr}")
            system(f"pipx uninstall plextraktsync@{pr}")

        click.echo(f"Updating PlexTraktSync to the pull request #{pr} version using pipx")
        system(f"pipx install --suffix=@{pr} --force git+https://github.com/Taxel/PlexTraktSync@refs/pull/{pr}/head")
        return

    click.echo("Updating PlexTraktSync to the latest version using pipx")
    system("pipx upgrade PlexTraktSync")
