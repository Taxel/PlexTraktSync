from urllib.parse import urlencode

from plextraktsync.util.openurl import openurl

URL_TEMPLATE = 'https://github.com/Taxel/PlexTraktSync/issues/new?template=bug.yml&{}'


def bug_url():
    from plextraktsync.util.versions import (pts_version, py_platform,
                                             py_version)

    q = urlencode({
        'os': py_platform(),
        'python': py_version(),
        'version': pts_version(),
    })

    return URL_TEMPLATE.format(q)


def bug_report():
    url = bug_url()

    print("Opening bug report URL in browser, if that doesn't work open the link manually:")
    print('')
    print(url)
    openurl(url)
