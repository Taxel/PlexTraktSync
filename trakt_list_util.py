from trakt.users import UserList
from trakt.errors import NotFoundException
from trakt.movies import Movie
import requests_cache
import logging
from plexapi.exceptions import BadRequest, NotFound
from itertools import count

class TraktList():
    def __init__(self, username, listname):
        self.name = listname
        self.plex_movies = []
        if username != None:
            self.slugs = dict(zip(map(lambda m: m.slug, [elem for elem in UserList._get(listname, username).get_items() if type(elem) == Movie]),count()))
    
    @staticmethod
    def from_slug_list(listname, slug_list):
        l = TraktList(None, listname)
        l.slugs = dict(zip(slug_list, count()))
        return l

    def addPlexMovie(self, slug, plex_movie):
        rank = self.slugs.get(slug)
        if rank is not None:
            self.plex_movies.append((rank, plex_movie))
            logging.info('Movie [{} ({})]: added to list {}'.format(plex_movie.title, plex_movie.year, self.name))

    def updatePlexList(self, plex):
        with requests_cache.disabled():
            try:
                plex.playlist(self.name).delete()
            except (NotFound, BadRequest):
                logging.error("Playlist %s not found, so it could not be deleted. Actual playlists: %s" % (self.name, plex.playlists()))
                pass
            if len(self.plex_movies) > 0:
                _, plex_movies_sorted = zip(*sorted(self.plex_movies))
                plex.createPlaylist(self.name, items=plex_movies_sorted)


class TraktListUtil():
    def __init__(self):
        self.lists = []

    def addList(self, username, listname, slug_list = None):
        if slug_list is not None:
            self.lists.append(TraktList.from_slug_list(listname, slug_list))
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
