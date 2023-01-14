from rich.table import Table

from plextraktsync.factory import factory


def watched_shows():
    trakt = factory.trakt_api
    print = factory.print

    table = Table(
        show_header=True, header_style="bold magenta", title="Watched shows on Trakt"
    )
    table.add_column("Id", style="dim", width=6)
    table.add_column("Slug")
    table.add_column("Seasons", justify="right")
    for show_id, progress in sorted(trakt.watched_shows.shows.items()):
        id = f"[link=https://trakt.tv/shows/{show_id}]{show_id}[/]"
        slug = f"[link=https://trakt.tv/shows/{progress.slug}]{progress.slug}[/]"
        table.add_row(id, slug, str(len(progress.seasons)))

    print(table)
