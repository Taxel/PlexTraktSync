from __future__ import annotations

from plextraktsync.commands.login import ensure_login
from plextraktsync.decorators.measure_time import measure_time
from plextraktsync.factory import factory, logger


def sync(
    sync_option: str,
    library: str,
    show: str,
    movie: str,
    ids: list[str],
    server: str,
    batch_delay: int,
    dry_run: bool,
    no_progress_bar: bool,
):
    """
    Perform sync between Plex and Trakt
    """

    logger.info(f"PlexTraktSync [{factory.version.full_version}]")
    logger.info("System-D journal: red:0", extra={"PRIORITY": "0"})
    logger.info("System-D journal: red:1", extra={"PRIORITY": "1"})
    logger.info("System-D journal: red:2", extra={"PRIORITY": "2"})
    logger.info("System-D journal: red:#", extra={"PRIORITY": "3"})
    logger.info("System-D journal: green", extra={"PRIORITY": "4"})
    logger.info("System-D journal: bold", extra={"PRIORITY": "5"})
    logger.info("System-D journal: norm:6", extra={"PRIORITY": "6"})
    logger.info("System-D journal: gray", extra={"PRIORITY": "7"})
    logger.info("System-D journal: norm:8", extra={"PRIORITY": "8"})

    movies = sync_option in ["all", "movies"]
    shows = sync_option in ["all", "tv", "shows"]
    watchlist = sync_option in ["all", "watchlist"]

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
    wc = factory.walk_config.update(movies=movies, shows=shows, watchlist=watchlist)
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
        print("Nothing to sync, this is likely due conflicting options given.")
        return

    with measure_time("Completed full sync"):
        runner = factory.sync
        if runner.config.need_library_walk:
            w.print_plan(print=logger.info)
        if dry_run:
            logger.info("Enabled dry-run mode: not making actual changes")
        runner.sync(walker=w, dry_run=config.dry_run)
