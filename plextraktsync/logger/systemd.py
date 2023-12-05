systemd_handler = None

try:
    from cysystemd.journal import JournaldLogHandler

    systemd_handler = JournaldLogHandler()
except ImportError:
    pass
