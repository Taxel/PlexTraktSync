from __future__ import annotations

import subprocess


def execx(command: str | list[str]):
    if isinstance(command, str):
        command = command.split(" ")

    process = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
    )
    return process.communicate()[0]
