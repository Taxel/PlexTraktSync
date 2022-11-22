from plextraktsync.console import print


def config(print=print):
    from plextraktsync.factory import factory
    config = factory.config

    print(f"# Config File: {config.config_yml}")
    config.dump(print=print)
