try:
    from functools import cached_property
except ImportError:
    from backports.cached_property import cached_property  # noqa: F401
