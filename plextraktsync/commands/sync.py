from typing import List

import click

from plextraktsync.commands.login import ensure_login
from plextraktsync.decorators.measure_time import measure_time
from plextraktsync.factory import factory, logger
from plextraktsync.version import version


def sync(
    sync_option: str,
    library: str,
    show: str,
    movie: str,
    ids: List[str],
    server: str,
    batch_delay: int,
    dry_run: bool,
    no_progress_bar: bool,
):
    """
    Perform sync between Plex and Trakt
    """

    logger.info(f"PlexTraktSync [{version()}]")

    movies = sync_option in ["all", "movies"]
    shows = sync_option in ["all", "tv", "shows"]

    config = factory.run_config.update(
        dry_run=dry_run,
    )
    if server:
        logger.warning('"plextraktsync sync --server=<name>" is deprecated use "plextraktsync --server=<name> sync"')
        config.update(server=server)
    if no_progress_bar:
        logger.warning('"plextraktsync sync --no-progress-bar" is deprecated use "plextraktsync --no-progressbar sync"')
        config.update(progress=False)
    if batch_delay:
        logger.warning(
            '"plextraktsync sync --batch-delay=<number>" is deprecated use "plextraktsync ---batch-delay=<number> sync"'
        )
        config.update(batch_delay=batch_delay)

    ensure_login()
    wc = factory.walk_config.update(movies=movies, shows=shows)
    w = factory.walker

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

    with measure_time("Completed full sync"):
        runner = factory.sync
        if runner.config.need_library_walk:
            w.print_plan(print=logger.info)
        if dry_run:
            logger.info("Enabled dry-run mode: not making actual changes")
        runner.sync(walker=w, dry_run=config.dry_run)
