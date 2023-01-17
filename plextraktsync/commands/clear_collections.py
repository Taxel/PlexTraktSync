

from plextraktsync.factory import factory, logger


def clear_collections(confirm: bool, dry_run: bool, collection: str):
    print = factory.print

    if not confirm and not dry_run:
        print("You need to pass --confirm or --dry-run option to proceed")
        return

    trakt = factory.trakt_api
    movies = collection in ["all", "movies"]
    shows = collection in ["all", "shows"]

    for movie in trakt.movie_collection if movies else []:
        logger.info(f"Deleting from Trakt: {movie}")
        if not dry_run:
            trakt.remove_from_collection(movie)

    for show in trakt.show_collection if shows else []:
        logger.info(f"Deleting from Trakt: {show}")
        if not dry_run:
            trakt.remove_from_collection(show)
