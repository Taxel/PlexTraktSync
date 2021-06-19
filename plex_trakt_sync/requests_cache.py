import requests
import requests_cache
from .path import trakt_cache

requests_cache.install_cache(trakt_cache)

session = requests.Session()