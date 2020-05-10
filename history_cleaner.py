from os import getenv, path
from config import CONFIG
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta

import sys
import getopt
import dateutil.parser
import requests_cache
import logging

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

    logLevel = logging.DEBUG if CONFIG['log_debug_messages'] else logging.INFO
    logging.basicConfig(
        format='%(asctime)s %(levelname)s:%(message)s',
        handlers=[logging.FileHandler('duplicate_cleaner.log', 'w', 'utf-8')],
        level=logLevel
    )
    analysis_span = 365
    days_to_clean = 0
    if len(argv):
        try:
            opts, args = getopt.getopt(argv, "hs:d:", ["span_start=", "days_to_clean="])
        except getopt.GetoptError:
            sys.exit(2)
        for opt, arg in opts:
            if opt == '-h':
                print(
                    'history_cleaner.py -d <number_of_days_back_to_clean> -s <span_of_days_to_consider_while_cleaning>'
                )
                sys.exit()
            elif opt in ("-s", "--span_start"):
                analysis_span = int(arg)
            elif opt in ("-d", "--days_to_clean"):
                days_to_clean = int(arg)

    # do not use the cache for account specific stuff as this is subject to change
    with requests_cache.disabled():
        trakt_user = trakt.users.User(getenv('TRAKT_USERNAME'))
        shows = trakt_user.watched_shows
        start_date = datetime.now(timezone.utc) - timedelta(days=analysis_span)
        history_ids_to_delete = []
        for show in shows:
            show_history = pytrakt_extensions.get_history(
                trakt_user.username,
                'shows',
                show.ids['ids']['trakt'],
                start_date,
                datetime.now(timezone.utc)
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
                    if not days_to_clean == 0:
                        within_range = list(filter(
                            lambda entry: (datetime.now(timezone.utc) - dateutil.parser.parse(
                                entry['history_entry']['watched_at'])).days < days_to_clean,
                            episode_plays))
                    else:
                        within_range = episode_plays
                    for episode_play in within_range:
                        logging.info(
                            "Play of episode {} - S{}E{} - {} that was mark as watched at: {} is scheduled for cleanup".format(
                                episode_play['history_entry']['show']['title'],
                                episode_play['history_entry']['episode']['season'],
                                episode_play['history_entry']['episode']['number'],
                                episode_play['history_entry']['episode']['title'],
                                episode_play['history_entry']['watched_at'],
                            ))
                    history_ids_to_delete = history_ids_to_delete + list(map(lambda entry: entry['id'], within_range))
        trakt.sync.remove_from_history(DummyRemoveIds(history_ids_to_delete))


if __name__ == "__main__":
    main(sys.argv[1:])
