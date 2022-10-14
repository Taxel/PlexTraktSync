from dataclasses import dataclass
from logging import Filter, LogRecord
from typing import Dict, List


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
    def __init__(self, rules: List[Dict]):
        super().__init__()
        self.rules = self.load_rules(rules or [])
        self.nrules = len(self.rules)

    def load_rules(self, rules: List[Dict]):
        filters = []
        for rule in rules:
            f = FilterRule(**rule)
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
