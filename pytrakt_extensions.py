from trakt.core import get
from trakt.tv import TVEpisode
import datetime

@get
def get_history(username, media_type, item_id, start_at: datetime = None, end_at: datetime = None, limit=50000):
    url = 'users/{username}/history/{type}/{item_id}?limit={limit}'.format(username=username, type=media_type, item_id=item_id, limit=limit)
    if start_at is not None and end_at is not None:
        url = url + '&start_at={start_at}Z&end_at={end_at}Z'.format(start_at=start_at.isoformat(), end_at=end_at.isoformat())

    data = yield url
    yield data

@get
def get_liked_lists():
    data = yield 'users/likes/lists'
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
    data = yield 'shows/{}/seasons?extended=episodes'.format(show.slug)
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
            self._instance = TVEpisode(self.show, self.season, number=self.number, **self.ids)
        return self._instance


@get
def watched(show_slug):
    # returns a ShowProgress object containing the watched states of the passed show
    data = yield 'shows/{}/progress/watched?specials=true&count_specials=true'.format(show_slug)
    yield ShowProgress(**data)

@get
def collected(show_slug):
    # returns a ShowProgress object containing the watched states of the passed show
    data = yield 'shows/{}/progress/collection'.format(show_slug)
    #print(data)
    yield ShowProgress(**data)

class EpisodeProgress():
    def __init__(self, number=0, aired=0, completed=False, last_watched_at=None, collected_at=None):
        self.number = number
        self.aired = aired
        self.completed = completed
        self.last_watched_at = last_watched_at
        self.collected_at = collected_at
        #print("Episode {} completed: {}".format(number, completed))

    def get_completed(self):
        return self.completed

class SeasonProgress():
    def __init__(self, number=0, aired=0, completed=False, episodes=None):
        self.number = number
        self.aired = aired
        self.episodes = {}
        for episode in episodes:
            prog = EpisodeProgress(**episode)
            self.episodes[prog.number] = prog

        self.completed = completed == len(episodes)
        #print("Season {} completed: {}".format(number, self.completed))

    def get_completed(self, episode):
        if self.completed:
            return True
        elif episode not in self.episodes.keys():
            return False
        return self.episodes[episode].get_completed()


class ShowProgress():
    def __init__(self, aired=0, completed=False, last_watched_at=None, reset_at=None, seasons=None, hidden_seasons=None, next_episode=0, last_episode=0, last_collected_at=None):
        self.aired = aired
        self.last_watched_at = last_watched_at
        self.last_collected_at = last_collected_at
        self.reset_at = reset_at
        self.hidden_seasons = hidden_seasons
        self.next_episode = next_episode
        self.last_episode = last_episode
        self.seasons = {}
        allCompleted = True
        for season in seasons:
            prog = SeasonProgress(**season)
            self.seasons[prog.number] = prog
            allCompleted = allCompleted and prog.completed

        self.completed = allCompleted if len(seasons) > 0 else False
        #print("Series completed: {}".format(self.completed))

    def get_completed(self, season, episode):
        if self.completed:
            return True
        elif season not in self.seasons.keys():
            return False
        return self.seasons[season].get_completed(episode)


if __name__ == "__main__":
    print(get_liked_lists())