import json
from json import JSONDecodeError
from os import system

import click

from plextraktsync.util.execx import execx


def pipx_installed(package: str):
    try:
        output = execx("pipx list --json")
    except FileNotFoundError:
        return None
    if not output:
        return None

    try:
        install_data = json.loads(output)
    except JSONDecodeError:
        return None
    if install_data is None:
        return None

    try:
        package = install_data["venvs"][package]["metadata"]["main_package"]
    except KeyError:
        return None

    return package


def enable_self_update():
    package = pipx_installed("plextraktsync")

    return package is not None


def self_update(pr: int):
    if pr:
        click.echo(f"Updating PlexTraktSync to the pull request #{pr} version using pipx")
        system(f"pipx install --suffix=@{pr} --force git+https://github.com/Taxel/PlexTraktSync@refs/pull/{pr}/head")
        return

    click.echo("Updating PlexTraktSync to the latest version using pipx")
    system("pipx upgrade PlexTraktSync")
