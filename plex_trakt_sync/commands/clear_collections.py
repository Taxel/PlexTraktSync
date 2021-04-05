import click
from plex_trakt_sync.clear_trakt_collections import clear_trakt_collections


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
