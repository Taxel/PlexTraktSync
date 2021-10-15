from os import getenv

_version = getenv("APP_VERSION")
if _version:
    __version__ = _version
else:
    __version__ = "0.15.x"
