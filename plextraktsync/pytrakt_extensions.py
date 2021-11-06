from trakt.core import get
from trakt.tv import TVEpisode


@get
def get_liked_lists():
    data = yield 'users/likes/lists?limit=1000'
    retVal = []
    for lst in data:
        thisList = {}
        thisList['listname'] = lst['list']['name']
        thisList['username'] = lst['list']['user']['ids']['slug']
        retVal.append(thisList)
    yield retVal


@get
def lookup_table(show):
    # returns all seasons and episodes with one single call
    data = yield 'shows/{}/seasons?extended=episodes'.format(show.trakt)
    retVal = {}
    for season in data:
        eps = {}
        if 'episodes' in season.keys():
            for episode in season['episodes']:
                eps[episode['number']] = LazyEpisode(show, season['number'], episode['number'], episode['ids'])
        retVal[season['number']] = eps
    yield retVal


class LazyEpisode():
    def __init__(self, show, season, number, ids):
        self.show = show
        self.season = season
        self.number = number
        self.ids = ids
        self._instance = None

    @property
    def instance(self):
        if self._instance is None:
            self._instance = TVEpisode(self.show.title, self.season, number=self.number, **self.ids)
        return self._instance


@get
def allwatched():
    # returns a ShowProgress object containing all watched episodes
    data = yield 'sync/watched/shows'
    yield AllWatchedShows(data)


@get
def watched(show_id):
    # returns a ShowProgress object containing the watched states of the passed show
    data = yield 'shows/{}/progress/watched?specials=true'.format(show_id)
    yield ShowProgress(**data)


@get
def collected(show_id):
    # returns a ShowProgress object containing the watched states of the passed show
    data = yield 'shows/{}/progress/collection?specials=true'.format(show_id)
    yield ShowProgress(**data)


class EpisodeProgress():
    def __init__(self, number=0, aired=0, plays=False, completed=False, last_watched_at=None, collected_at=None):
        self.number = number
        self.aired = aired
        self.completed = completed
        if plays > 0:
            self.completed = True
        self.last_watched_at = last_watched_at
        self.collected_at = collected_at

    def get_completed(self):
        return self.completed


class SeasonProgress():
    def __init__(self, number=0, title=None, aired=0, completed=False, episodes=None):
        self.number = number
        self.aired = aired
        self.episodes = {}
        for episode in episodes:
            prog = EpisodeProgress(**episode)
            self.episodes[prog.number] = prog

        self.completed = completed == len(episodes)

    def get_completed(self, episode):
        if self.completed:
            return True
        elif episode not in self.episodes.keys():
            return False
        return self.episodes[episode].get_completed()


class ShowProgress():
    def __init__(self, aired=0, plays=None, completed=False, last_watched_at=None, last_updated_at=None, reset_at=None, show=None, seasons=None, hidden_seasons=None, next_episode=0, last_episode=0, last_collected_at=None):
        self.aired = aired
        self.last_watched_at = last_watched_at
        self.last_updated_at = last_updated_at
        self.last_collected_at = last_collected_at
        self.reset_at = reset_at
        self.hidden_seasons = hidden_seasons
        self.next_episode = next_episode
        self.last_episode = last_episode
        self.trakt = show['ids']['trakt'] if show else None
        self.slug = show['ids']['slug'] if show else None
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
        return self.seasons[season].get_completed(episode)


class AllWatchedShows():
    def __init__(self, shows=None):
        self.shows = {}
        for show in shows:
            prog = ShowProgress(**show)
            self.shows[prog.trakt] = prog

    def get_completed(self, trakt_id, season, episode):
        if trakt_id not in self.shows.keys():
            return False
        elif season not in self.shows[trakt_id].seasons.keys():
            return False
        return self.shows[trakt_id].seasons[season].get_completed(episode)

    def add(self, trakt_id, season, episode):
        episode_prog = {"number":episode, "completed":True}
        season_prog = {"number":season, "episodes":[episode_prog]}
        if trakt_id in self.shows:
            if season in self.shows[trakt_id].seasons:
                self.shows[trakt_id].seasons[season].episodes[episode] = EpisodeProgress(**episode_prog)
            else:
                self.shows[trakt_id].seasons[season] = SeasonProgress(**season_prog)
        else:
            self.shows[trakt_id] = ShowProgress(seasons=[season_prog])


if __name__ == "__main__":
    print(get_liked_lists())
