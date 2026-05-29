from __future__ import annotations

import re
import sys
import time
from datetime import datetime

from plextraktsync.factory import factory

# Matches log level in the file format: "%(asctime)-15s %(levelname)s[%(name)s]:%(message)s"
ERROR_RE = re.compile(r"\b(?:ERROR|CRITICAL)\[")
LOG_TIMESTAMP_RE = re.compile(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})")

_TAIL_BYTES_PER_SECOND = 256


def healthcheck(max_age: int):
    log_file = factory.config.log_file
    cutoff = time.time() - max_age
    last_error = None

    tail_bytes = max_age * _TAIL_BYTES_PER_SECOND

    try:
        with open(log_file, "rb") as f:
            f.seek(0, 2)
            size = f.tell()
            if size > tail_bytes:
                f.seek(size - tail_bytes)
                f.readline()  # discard partial line at seek point
            content = f.read().decode("utf-8", errors="replace")
    except FileNotFoundError:
        print(f"Log file not found: {log_file}", file=sys.stderr)
        raise SystemExit(1)

    for line in content.splitlines():
        if not ERROR_RE.search(line):
            continue
        m = LOG_TIMESTAMP_RE.match(line)
        if m:
            try:
                ts = datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S")
                if ts.timestamp() < cutoff:
                    continue
            except ValueError:
                pass  # unparseable timestamp: treat as recent
        last_error = line.strip()

    if last_error:
        print(f"Healthcheck failed: {last_error}", file=sys.stderr)
        raise SystemExit(1)

    print("Healthcheck passed")
