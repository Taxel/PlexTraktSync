from __future__ import annotations

from plextraktsync.factory import factory
from plextraktsync.util.execp import execp
from plextraktsync.util.packaging import backend_for_name, list_managed_installs, managed_installs_by_backend, program_name


def pr_number() -> int | None:
    """
    Check if current executable is named plextraktsync@<pr>
    """

    try:
        pr = program_name().split("@")[1]
    except IndexError:
        return None

    if pr.isnumeric():
        return int(pr)
    return None


def self_update(pr: int):
    print = factory.print

    if not pr:
        pr = pr_number()
        if pr:
            print(f"Installed as pr #{pr}, enabling pr mode")

    installs = list_managed_installs()
    if not installs:
        print("No managed PlexTraktSync installation found in pipx or uv")
        return

    if pr:
        for backend_name, backend_installs in managed_installs_by_backend().items():
            backend = backend_for_name(backend_name)
            if backend is None:
                continue

            print(f"Updating PlexTraktSync using {backend_name} to pull request #{pr}")
            commands = backend.pr_update_commands(pr, backend_installs)
            for command in commands:
                print(f"Running [{backend_name}] {command}")
                execp(command)
        return

    for install in installs:
        backend = backend_for_name(install.backend)
        if backend is None:
            continue

        print(f"Updating PlexTraktSync install '{install.app_name}' using {install.backend}")
        execp(backend.latest_update_command(install))
