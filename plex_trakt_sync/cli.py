import click
from plex_trakt_sync.main import main
from plex_trakt_sync.clear_trakt_collections import clear_trakt_collections


@click.group()
def cli():
    """
    Plex-Trakt-Sync is a two-way-sync between trakt.tv and Plex Media Server
    """
    pass


@click.command()
def sync():
    """
    Perform sync between Plex and Trakt
    """

    main()


@click.command()
@click.option('--confirm', is_flag=True, help='Confirm the dangerous action')
def clear_collections(confirm):
    """
    Clear Movies and Shows collections in Trakt
    """

    if not confirm:
        click.echo('You need to pass --confirm option to proceed')
        return
    clear_trakt_collections()


cli.add_command(sync)
cli.add_command(clear_collections)
