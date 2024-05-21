import asyncio

from decorator import decorator


@decorator
def coro(f, *args, **kwargs):
    """
    Decorator to get started with async/await with click

    https://github.com/pallets/click/issues/85#issuecomment-503464628
    """
    return asyncio.run(f(*args, **kwargs))
