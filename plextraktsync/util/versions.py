def py_version():
    from platform import python_version

    return python_version()


def py_platform():
    from platform import platform

    return platform(terse=True, aliased=True)


def plex_api_version():
    from plexapi import VERSION

    return VERSION


def trakt_api_version():
    from trakt import __version__

    return __version__


def pts_version():
    from plextraktsync import __version__

    return __version__
