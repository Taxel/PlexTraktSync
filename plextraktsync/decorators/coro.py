import asyncio
from functools import wraps


def coro(f):
    """
    Decorator to get started with async/await with click

    https://github.com/pallets/click/issues/85#issuecomment-503464628
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))

    return wrapper
