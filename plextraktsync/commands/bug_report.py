from urllib.parse import urlencode

from plextraktsync.util.openurl import openurl

URL_TEMPLATE = "https://github.com/Taxel/PlexTraktSync/issues/new?template=bug.yml&{}"


def bug_url():
    from plextraktsync.factory import factory

    config = factory.config
    version = factory.version

    q = urlencode(
        {
            "os": version.py_platform,
            "python": version.py_version,
            "version": version.full_version,
            "config": config.dump(),
        }
    )

    return URL_TEMPLATE.format(q)


def bug_report():
    url = bug_url()

    print(
        "Opening bug report URL in browser, if that doesn't work open the link manually:"
    )
    print("")
    print(url)
    openurl(url)
