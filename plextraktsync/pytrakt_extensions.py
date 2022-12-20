from trakt.core import get
from trakt.utils import airs_date


@get
def allwatched():
    # returns a AllShowProgress object containing all watched shows
    data = yield "sync/watched/shows"
    yield AllShowsProgress(data)


@get
def allcollected():
    # returns a AllShowProgress object containing all collected shows
    data = yield "sync/collection/shows"
    yield AllShowsProgress(data)


class EpisodeProgress:
    def __init__(
        self,
        number=0,
        aired=0,
        plays=False,
        completed=False,
        last_watched_at=None,
        collected_at=None,
    ):
        self.number = number
        self.aired = aired
        self.completed = completed
        if plays > 0:
            self.completed = True
        self.last_watched_at = last_watched_at
        self.collected_at = collected_at

    def get_completed(self):
        return self.completed


class SeasonProgress:
    def __init__(self, number=0, title=None, aired=0, completed=False, episodes=None):
        self.number = number
        self.aired = aired
        self.episodes = {}
        for episode in episodes:
            prog = EpisodeProgress(**episode)
            self.episodes[prog.number] = prog

        self.completed = completed == len(episodes)

    def get_completed(self, episode, reset_at):
        if self.completed:
            return True
        elif episode not in self.episodes.keys():
            return False
        last_watched_at = airs_date(self.episodes[episode].last_watched_at)
        if reset_at and reset_at > last_watched_at:
            return False
        return self.episodes[episode].get_completed()


class ShowProgress:
    def __init__(
        self,
        aired=0,
        plays=None,
        completed=False,
        last_watched_at=None,
        last_updated_at=None,
        reset_at=None,
        show=None,
        seasons=None,
        hidden_seasons=None,
        next_episode=0,
        last_episode=0,
        last_collected_at=None,
    ):
        self.aired = aired
        self.last_watched_at = last_watched_at
        self.last_updated_at = last_updated_at
        self.last_collected_at = last_collected_at
        self.reset_at = reset_at
        self.hidden_seasons = hidden_seasons
        self.next_episode = next_episode
        self.last_episode = last_episode
        self.trakt = show["ids"]["trakt"] if show else None
        self.slug = show["ids"]["slug"] if show else None
        self.seasons = {}
        allCompleted = True
        for season in seasons:
            prog = SeasonProgress(**season)
            self.seasons[prog.number] = prog
            allCompleted = allCompleted and prog.completed

        self.completed = allCompleted if len(seasons) > 0 else False

    def get_completed(self, season, episode):
        if self.completed:
            return True
        elif season not in self.seasons.keys():
            return False
        reset_at = airs_date(self.reset_at)
        return self.seasons[season].get_completed(episode, reset_at)


class AllShowsProgress:
    def __init__(self, shows=None):
        self.shows = {}
        for show in shows:
            prog = ShowProgress(**show)
            self.shows[prog.trakt] = prog

    def get_completed(self, trakt_id, season, episode):
        if trakt_id not in self.shows.keys():
            return False
        else:
            return self.shows[trakt_id].get_completed(season, episode)

    def is_collected(self, trakt_id, season, episode):
        if trakt_id not in self.shows.keys():
            return False
        elif season not in self.shows[trakt_id].seasons.keys():
            return False
        return episode in self.shows[trakt_id].seasons[season].episodes.keys()

    def reset_at(self, trakt_id):
        if trakt_id not in self.shows.keys():
            return None
        else:
            return airs_date(self.shows[trakt_id].reset_at)

    def add(self, trakt_id, season, episode):
        episode_prog = {"number": episode, "completed": True}
        season_prog = {"number": season, "episodes": [episode_prog]}
        if trakt_id in self.shows:
            if season in self.shows[trakt_id].seasons:
                self.shows[trakt_id].seasons[season].episodes[episode] = EpisodeProgress(**episode_prog)
            else:
                self.shows[trakt_id].seasons[season] = SeasonProgress(**season_prog)
        else:
            self.shows[trakt_id] = ShowProgress(seasons=[season_prog])
