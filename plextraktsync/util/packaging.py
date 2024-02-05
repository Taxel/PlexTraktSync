import json
import site
from json import JSONDecodeError
from os.path import dirname

from plextraktsync.util.execx import execx


def installed():
    """
    Return true if this package is installed to site-packages
    """
    absdir = dirname(dirname(dirname(__file__)))
    paths = site.getsitepackages()

    return absdir in paths


def pip_installed(name: str):
    import sys

    try:
        output = execx(f"{sys.executable} -m pip inspect")
    except FileNotFoundError:
        return None

    try:
        inspect = json.loads(output)
    except JSONDecodeError:
        return None

    for package in inspect["installed"]:
        if package["metadata"]["name"] != name:
            continue
        return package

    return None


def pipx_installed(package: str):
    try:
        output = execx("pipx list --json")
    except FileNotFoundError:
        return None
    if not output:
        return None

    try:
        install_data = json.loads(output)
    except JSONDecodeError:
        return None
    if install_data is None:
        return None

    try:
        package = install_data["venvs"][package]["metadata"]["main_package"]
    except KeyError:
        return None

    return package


def program_name():
    """
    Return current program name:
    - pipx: plextraktsync
    - pipx for pr 1000: plextraktsync@1000
    """

    import sys
    from os.path import basename

    return basename(sys.argv[0])


def vcs_info(package: str):
    """
    Return vcs_info from direct_url.json of a .dist-info for the package
    """
    data = pip_installed(package)
    if not data:
        return None
    try:
        v = data["direct_url"]["vcs_info"]
    except KeyError:
        return None

    v["pr"] = v["requested_revision"][10:-5]
    v["short_commit_id"] = v["commit_id"][:8]

    return v
