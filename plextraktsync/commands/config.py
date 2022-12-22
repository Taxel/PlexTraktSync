from plextraktsync.console import print


def dump(data, print=None):
    """
    Print config serialized as yaml.
    If print is None, return the produced string instead.
    """
    from plextraktsync.config.ConfigLoader import ConfigLoader

    dump = ConfigLoader.dump_yaml(None, data)
    if print is None:
        return dump
    print(dump)


def config(urls_expire_after: bool, print=print):
    from plextraktsync.factory import factory
    config = factory.config

    if urls_expire_after:
        print("# HTTP Cache")
        config.http_cache.dump(print=print)
        return

    print(f"# Config File: {config.config_yml}")
    config.dump(print=print)
