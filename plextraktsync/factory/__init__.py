from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .Factory import Factory

if TYPE_CHECKING:
    import logging as logging_module

    logger: logging_module.Logger
    logging: Any

factory = Factory()

# Resolved on first access rather than at import time. Touching factory.logger
# or factory.logging eagerly here loaded the config and initialized logging
# (pulling in yaml, dotenv and rich.logging) for anything that imported this
# module, including `plextraktsync.cli` for `--help`. Commands are lazily
# loaded, so the modules that do `from plextraktsync.factory import logging`
# only trigger this when they actually run.
_LAZY = frozenset({"logger", "logging"})


def __getattr__(name: str) -> Any:
    if name in _LAZY:
        value = getattr(factory, name)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted({*globals(), *_LAZY})
