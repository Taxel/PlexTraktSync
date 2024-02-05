# minimal version of openurl without six dependency
# https://github.com/panda2134/open-python/blob/32a4b61b44302da185dcf6a72a48d1c726eb3e51/open_python/__init__.py
import sys

from plextraktsync.util.execx import execx


def openurl(url: str):
    try:
        opener = {
            "darwin": "open",
            "win32": "start",
        }[sys.platform]
    except KeyError:
        opener = "xdg-open"

    try:
        execx([opener, url])
    except FileNotFoundError:
        return False

    return True
