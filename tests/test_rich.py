#!/usr/bin/env python3 -m pytest
import sys
from os.path import dirname, abspath
# from rich import print

from rich.console import Console
from rich.markup import render
from rich.style import Style

from plex_trakt_sync.commands.sync import sync_collection, sync_ratings, sync_watched
from plex_trakt_sync.factory import factory
from plex_trakt_sync.media import MediaFactory
from plex_trakt_sync.plex_api import PlexApi
from plex_trakt_sync.trakt_api import TraktApi
from plex_trakt_sync.version import git_version_info

console = Console()

test_data = [
    {"jsonrpc": "2.0", "method": "sum", "params": [None, 1, 2, 4, False, True], "id": "1", },
    {"jsonrpc": "2.0", "method": "notify_hello", "params": [7]},
    {"jsonrpc": "2.0", "method": "subtract", "params": [42, 23], "id": "2"},
]


def test_rich():
    b = 1
    d = globals()
    print("Hello, [bold magenta]World[/bold magenta]!", ":vampire:", locals())
    console.print("Hello", "World!")
    console.print("Hello", "World!", style="bold red")
    console.print("Where there is a [bold cyan]Will[/bold cyan] there [u]is[/u] a [i]way[/i].")


def test_link():
    # https://www.willmcgugan.com/blog/tech/post/real-working-hyperlinks-in-the-terminal-with-rich/
    print("Visit my [link=https://www.willmcgugan.com]blog[/link]!")


def test_fmt():
    print(Style.parse("bold link https://example.org"))
    # print(Style.parse("Visit my [link=https://www.willmcgugan.com]blog[/link]!"))
    print(Style(link="foo"))

    result = render("[link=https://example.org]FOO[/link]")
    print(type(result))
    print(result)
    console.print(result)


def test_table():
    # https://rich.readthedocs.io/en/latest/tables.html
    from rich.console import Console
    from rich.table import Table

    table = Table(title="Star Wars Movies")

    table.add_column("Released", justify="right", style="cyan", no_wrap=True)
    table.add_column("Title", style="magenta")
    table.add_column("Box Office", justify="right", style="green")

    table.add_row("Dec 20, 2019", "Star Wars: The Rise of Skywalker", "$952,110,690")
    table.add_row("May 25, 2018", "Solo: A Star Wars Story", "$393,151,347")
    table.add_row("Dec 15, 2017", "Star Wars Ep. V111: The Last Jedi", "$1,332,539,889")
    table.add_row("Dec 16, 2016", "Rogue One: A Star Wars Story", "$1,332,439,889")

    console = Console()
    console.print(table)


def test_log():
    enabled = False
    context = {
        "foo": "bar",
    }
    movies = ["Deadpool", "Rise of the Skywalker"]
    console.log("Hello from", console, "!")
    console.log(test_data, log_locals=True)


def test_run():
    from time import sleep
    from rich.panel import Panel
    from rich.progress import Progress

    git_version = git_version_info()
    # logger.info(f"Syncing with Plex {CONFIG['PLEX_USERNAME']} and Trakt {CONFIG['TRAKT_USERNAME']}")

    # JOBS = [100, 150, 25, 70, 110, 90]

    progress = Progress(auto_refresh=False)
    master_task = progress.add_task("", total=2)
    # jobs_task = progress.add_task("jobs")

    progress.console.print(
        Panel(
            f"[bold blue]PlexTraktSync[/] [blue]{git_version}",
            padding=1,
        )
    )

    with progress:
        plex = factory.plex_api()
        trakt = factory.trakt_api()
        mf = factory.media_factory()

        progress.log(f"Sync movies")

        for section in plex.movie_sections():
            show_task = progress.add_task(f"{section.title}")
            progress.start_task(show_task)

            for pm in progress.track(section.items(), total=len(section), task_id=show_task):
                m = mf.resolve_any(pm)
                if not m:
                    continue
                sync_collection(m)
                sync_ratings(m)
                sync_watched(m)

            progress.advance(master_task, 1)
            progress.log(f"Completed {section.title}")

        progress.log(f"Sync Shows")
        for section in plex.show_sections():
            show_task = progress.add_task(f"{section.title}")
            progress.start_task(show_task)
            for pm in progress.track(section.items(), total=len(section), task_id=show_task):
                m = mf.resolve_any(pm)
                if not m:
                    continue

                # episode_task = progress.add_task(f"{m.plex.item.title}")
                # for pe in progress.track(list(m.plex.episodes()), task_id=episode_task):
                for pe in m.plex.episodes():
                    me = mf.resolve_any(pe, m.trakt)
                    if not me:
                        continue
                    me.show = m

                    sync_collection(me)
                    sync_watched(me)
                    # progress.advance(show_task, 1)

            progress.advance(master_task, 1)
            progress.log(f"Completed {section.title}")

        trakt.flush()

        progress.log(
            Panel(":sparkle: All done! :sparkle:", border_style="green", padding=1)
        )


if __name__ == "__main__":
    # test_rich()
    # test_log()
    # test_link()
    # test_table()
    # test_fmt()
    test_run()
