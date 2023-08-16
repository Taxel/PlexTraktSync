from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property
from logging import Filter
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from logging import Logger, LogRecord


@dataclass
class FilterRule:
    """
    Structure to hold log filters
    """

    # filter by name
    name: str = None
    # filter by level
    level: bool = False
    # filter by message
    message: str = None


# https://stackoverflow.com/a/879937/2314626
class LoggerFilter(Filter):
    def __init__(self, rules: list[dict], logger: Logger):
        super().__init__()
        self.logger = logger
        self.rules = self.build_rules(rules or [])

    @cached_property
    def nrules(self):
        return len(self.rules)

    def build_rules(self, rules):
        filters = []
        for rule in rules:
            try:
                f = FilterRule(**rule)
            except TypeError as e:
                self.logger.error(f"Skip rule: {type(e).__name__}: {e}")
                continue
            filters.append(f)
        return filters

    def filter(self, record: LogRecord):
        # quick check to skip filtering
        if not self.nrules:
            return True

        message = record.getMessage()
        for rule in self.rules:
            matched = False
            # Filter by level
            if rule.level:
                if rule.level == record.levelname:
                    matched = True
                else:
                    continue
            # Filter by name
            if rule.name:
                if rule.name == record.name:
                    matched = True
                else:
                    continue
            # Filter by message
            if rule.message:
                if rule.message in message:
                    matched = True
                else:
                    continue

            if matched:
                return False
        return True
