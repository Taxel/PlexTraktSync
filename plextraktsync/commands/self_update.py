import json
import subprocess
from json import JSONDecodeError
from os import system
from typing import List, Union

import click

from plextraktsync.version import version as get_version


def execx(command: Union[str, List[str]]):
    if isinstance(command, str):
        command = command.split(' ')

    process = subprocess.Popen(command, stdout=subprocess.PIPE)
    return process.communicate()[0]


def pipx_installed(package: str):
    try:
        output = execx('pipx list --json')
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
        package = install_data['venvs'][package]['metadata']['main_package']
    except KeyError:
        return None

    return package


def enable_self_update():
    package = pipx_installed('plextraktsync')

    return package is not None


@click.command()
def self_update():
    """
    Update PlexTraktSync to latest version using pipx

    \b
    $ plextraktsync self-update
    Updating PlexTraktSync to latest using pipx
    upgraded package plextraktsync from 0.15.3 to 0.18.5 (location: /Users/glen/.local/pipx/venvs/plextraktsync)
    """

    click.echo('Updating PlexTraktSync to latest using pipx')
    system('pipx upgrade PlexTraktSync')
