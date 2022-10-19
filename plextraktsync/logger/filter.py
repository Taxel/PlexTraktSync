from dataclasses import dataclass
from logging import Filter, Logger, LogRecord
from typing import Dict, List

from plextraktsync.decorators.cached_property import cached_property


@dataclass
class FilterRule:
    """
    Structure to hold log filters
    """

    # filter by level
    level: bool = False
    # filter by message
    message: str = None


# https://stackoverflow.com/a/879937/2314626
class LoggerFilter(Filter):
    def __init__(self, rules: List[Dict], logger: Logger):
        super().__init__()
        self.logger = logger
        self._rules = rules or []

    @cached_property
    def nrules(self):
        return len(self.rules)

    @cached_property
    def rules(self):
        filters = []
        for rule in self._rules:
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
            # Filter by message
            if rule.message:
                if rule.message in message:
                    matched = True
                else:
                    continue

            if matched:
                return False
        return True
