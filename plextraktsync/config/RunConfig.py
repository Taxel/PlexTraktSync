from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RunConfig:
    """
    Class to hold runtime config parameters
    """

    dry_run: bool = False
    batch_delay: int = 5
    progressbar: bool = True
    cache: bool = True
    server: str | None = None

    def update(self, **kwargs):
        for name, value in kwargs.items():
            self.__setattr__(name, value)

        return self
