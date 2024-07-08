from __future__ import annotations

from subprocess import call


def execp(command: str):
    print(command)
    call(command, shell=True)
