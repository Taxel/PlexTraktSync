from typing import List

import click

from plextraktsync.commands.login import ensure_login
from plextraktsync.decorators.measure_time import measure_time
from plextraktsync.factory import factory
from plextraktsync.logging import logger
from plextraktsync.version import version


def sync(
    sync_option: str,
    library: str,
    show: str,
    movie: str,
    ids: List[str],
    batch_delay: int,
    dry_run: bool,
    no_progress_bar: bool,
):
    """
    Perform sync between Plex and Trakt
    """

    logger.info(f"PlexTraktSync [{version()}]")
    ensure_login()

    movies = sync_option in ["all", "movies"]
    shows = sync_option in ["all", "tv", "shows"]

    config = factory.run_config().update(
        batch_delay=batch_delay, dry_run=dry_run, progressbar=not no_progress_bar
    )
    wc = factory.walk_config().update(movies=movies, shows=shows)
    w = factory.walker()

    if ids:
        for id in ids:
            wc.add_id(id)
    if library:
        wc.add_library(library)
    if show:
        wc.add_show(show)
    if movie:
        wc.add_movie(movie)

    if not wc.is_valid():
        click.echo("Nothing to sync, this is likely due conflicting options given.")
        return

    w.print_plan(print=logger.info)

    if dry_run:
        logger.info("Enabled dry-run mode: not making actual changes")

    with measure_time("Completed full sync"):
        runner = factory.sync()
        runner.sync(walker=w, dry_run=config.dry_run)
