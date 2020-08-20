from trakt.users import UserList
from trakt.errors import NotFoundException
from trakt.movies import Movie
import requests_cache
import logging
from plexapi.exceptions import BadRequest, NotFound

class TraktList():
    def __init__(self, username, listname):
        self.name = listname
        self.plex_movies = []
        self.list_order = []
        if username != None:
            self.slugs = list(map(lambda m: m.slug, [elem for elem in UserList._get(listname, username).get_items() if type(elem) == Movie]))
    
    @staticmethod
    def from_set(listname, list_set):
        l = TraktList(None, listname)
        l.slugs = list_set
        return l

    def addPlexMovie(self, slug, plex_movie):
        if slug in self.slugs:
            self.plex_movies.append(plex_movie)
            self.list_order.append(self.slugs.index(slug))
            logging.info('Movie [{} ({})]: added to list {}'.format(plex_movie.title, plex_movie.year, self.name))

    def updatePlexList(self, plex):
        with requests_cache.disabled():
            try:
                plex.playlist(self.name).delete()
            except (NotFound, BadRequest):
                logging.error("Playlist %s not found, so it could not be deleted. Actual playlists: %s" % (self.name, plex.playlists()))
                pass
            if len(self.plex_movies) > 0:
                _, plex_movies_sorted = zip(*sorted(zip(self.list_order, self.plex_movies)))
                plex.createPlaylist(self.name, items=plex_movies_sorted)


class TraktListUtil():
    def __init__(self):
        self.lists = []

    def addList(self, username, listname, list_set = None):
        if list_set is not None:
            self.lists.append(TraktList.from_set(listname, list_set))
            logging.info("Downloaded List {}".format(listname))
            return
        try:
            self.lists.append(TraktList(username, listname))
            logging.info("Downloaded List {}".format(listname))
        except NotFoundException:
            logging.warning("Failed to get list {} by user {}".format(listname, username))

    def addPlexMovieToLists(self, slug, plex_movie):
        for l in self.lists:
            l.addPlexMovie(slug, plex_movie)

    def updatePlexLists(self, plex):
        for l in self.lists:
            l.updatePlexList(plex)
