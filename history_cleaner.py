from os import getenv, path
from dotenv import load_dotenv

import sys
import getopt
import datetime
import requests_cache

import trakt

trakt.core.CONFIG_PATH = path.join(path.dirname(path.abspath(__file__)), ".pytrakt.json")

import trakt.users
import trakt.sync
import trakt.tv

import pytrakt_extensions


class DummyRemoveIds(object):
    """A Class used as a dummy class to use PyTrakt"""

    def __init__(self, ids):
        super(DummyRemoveIds, self).__init__()
        self.ids = ids

    def to_json(self):
        return {'ids': self.ids}


def main(argv):
    load_dotenv()
    if not getenv("PLEX_TOKEN") or not getenv("TRAKT_USERNAME"):
        print("First run, please follow those configuration instructions.")
        load_dotenv()

    days_back = 60
    if len(argv):
        try:
            opts, args = getopt.getopt(argv, "hd:", ["days="])
        except getopt.GetoptError:
            sys.exit(2)
        for opt, arg in opts:
            if opt == '-h':
                print('history_cleaner.py -d <number_of_days_back_to_clean>')
                sys.exit()
            elif opt in ("-d", "--days"):
                days_back = int(arg)

    # do not use the cache for account specific stuff as this is subject to change
    with requests_cache.disabled():
        trakt_user = trakt.users.User(getenv('TRAKT_USERNAME'))
        shows = trakt_user.watched_shows
        year_ago = datetime.datetime.now() - datetime.timedelta(days=days_back)
        history_ids_to_delete = []
        for show in shows:
            show_history = pytrakt_extensions.get_history(
                trakt_user.username,
                'shows',
                show.ids['ids']['trakt'],
                year_ago,
                datetime.datetime.now()
            )

            by_episode = {}
            for history_entry in show_history:
                if not history_entry['episode']['ids']['trakt'] in by_episode.keys():
                    by_episode[history_entry['episode']['ids']['trakt']] = []
                episode = {
                    'id': history_entry['id'],
                    'history_entry': history_entry
                }
                by_episode[history_entry['episode']['ids']['trakt']].append(episode)

            for episode_plays_key in by_episode:
                episode_plays = by_episode[episode_plays_key]
                if len(episode_plays) > 1:
                    oldest_play = min(episode_plays, key=lambda entry: entry['id'])
                    episode_plays.remove(oldest_play)
                    history_ids_to_delete = history_ids_to_delete + list(map(lambda entry: entry['id'], episode_plays))
        trakt.sync.remove_from_history(DummyRemoveIds(history_ids_to_delete))


if __name__ == "__main__":
    main(sys.argv[1:])
