import site
from os.path import dirname


def installed():
    """
    Return true if this package is installed to site-packages
    """
    absdir = dirname(dirname(dirname(__file__)))
    paths = site.getsitepackages()

    return absdir in paths
