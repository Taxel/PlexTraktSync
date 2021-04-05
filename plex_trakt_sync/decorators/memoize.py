try:
    from functools import cache as memoize
except ImportError:
    # For py<3.9
    # https://docs.python.org/3.9/library/functools.html
    from functools import lru_cache as memoize
