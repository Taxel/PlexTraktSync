from os import system

import click


@click.command()
def self_update():
    """
    Update PlexTraktSync to latest version using pipx

    $ plextraktsync self-update
    Updating PlexTraktSync to latest using pipx
    upgraded package plextraktsync from 0.15.3 to 0.18.5 (location: /Users/glen/.local/pipx/venvs/plextraktsync)
    """

    click.echo('Updating PlexTraktSync to latest using pipx')
    system('pipx upgrade PlexTraktSync')
