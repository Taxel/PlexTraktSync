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


def config(print=print):
    from plextraktsync.factory import factory
    config = factory.config

    print(f"# Config File: {config.config_yml}")
    config.dump(print=print)

    print("# HTTP Cache")
    config.http_cache.dump(print=print)
