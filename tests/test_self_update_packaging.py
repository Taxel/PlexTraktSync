#!/usr/bin/env python3 -m pytest
from __future__ import annotations

import json

import pytest

from plextraktsync.commands import self_update as self_update_command
from plextraktsync.factory.Factory import Factory
from plextraktsync.util import packaging
from plextraktsync.util.packaging import ManagedInstall


def test_pipx_detection(monkeypatch):
    pipx_data = {
        "venvs": {
            "PlexTraktSync": {
                "metadata": {
                    "main_package": {
                        "package": "PlexTraktSync",
                        "package_or_url": "PlexTraktSync",
                        "apps": ["plextraktsync"],
                    }
                }
            },
            "OtherTool": {
                "metadata": {
                    "main_package": {
                        "package": "OtherTool",
                        "package_or_url": "OtherTool",
                        "apps": ["othertool"],
                    }
                }
            },
        }
    }

    def fake_execx(command):
        if command == "pipx list --json":
            return json.dumps(pipx_data).encode("utf-8")
        if command.startswith("uv tool list"):
            return b""
        raise AssertionError(command)

    monkeypatch.setattr(packaging, "execx", fake_execx)

    installs = packaging.list_managed_installs()
    assert len(installs) == 1
    assert installs[0].backend == "pipx"
    assert installs[0].app_name == "plextraktsync"


def test_uv_detection(monkeypatch):
    uv_output = "\n".join(
        [
            "plextraktsync v0.35.0 [required:  PlexTraktSync] [CPython 3.12.3] (/tmp/uv/plextraktsync)",
            "- plextraktsync (/tmp/bin/plextraktsync)",
            "plextraktsync-pr v0.35.0.dev0 [required:  git+https://github.com/Taxel/PlexTraktSync@refs/pull/838/head] [CPython 3.12.3] (/tmp/uv/plextraktsync-pr)",
            "- plextraktsync-pr (/tmp/bin/plextraktsync-pr)",
        ]
    ).encode("utf-8")

    def fake_execx(command):
        if command == "pipx list --json":
            return b""
        if command.startswith("uv tool list"):
            return uv_output
        raise AssertionError(command)

    monkeypatch.setattr(packaging, "execx", fake_execx)

    installs = packaging.list_managed_installs()
    assert len(installs) == 2
    assert installs[0].backend == "uv"
    assert installs[0].pr is None
    assert installs[1].backend == "uv"
    assert installs[1].pr == 838


@pytest.mark.parametrize(
    ("installs", "enabled"),
    [
        ([ManagedInstall(backend="pipx", app_name="plextraktsync", package_name="PlexTraktSync")], True),
        ([ManagedInstall(backend="uv", app_name="plextraktsync", package_name="PlexTraktSync")], True),
        (
            [
                ManagedInstall(backend="pipx", app_name="plextraktsync", package_name="PlexTraktSync"),
                ManagedInstall(backend="uv", app_name="plextraktsync", package_name="PlexTraktSync"),
            ],
            True,
        ),
        ([], False),
    ],
)
def test_enable_self_update(monkeypatch, installs, enabled):
    monkeypatch.setattr(packaging, "list_managed_installs", lambda: installs)
    monkeypatch.setattr(packaging, "managed_install_for_program", lambda name=None: installs[0] if installs else None)
    assert Factory().enable_self_update is enabled


def test_self_update_latest_across_backends(monkeypatch):
    installs = [
        ManagedInstall(backend="pipx", app_name="plextraktsync", package_name="PlexTraktSync"),
        ManagedInstall(backend="uv", app_name="plextraktsync", package_name="PlexTraktSync"),
    ]
    executed = []

    class DummyBackend:
        def __init__(self, command):
            self.command = command

        def latest_update_command(self, install):
            return self.command

    backends = {
        "pipx": DummyBackend("pipx upgrade plextraktsync"),
        "uv": DummyBackend("uv tool upgrade plextraktsync"),
    }

    monkeypatch.setattr(self_update_command, "list_managed_installs", lambda: installs)
    monkeypatch.setattr(self_update_command, "backend_for_name", lambda name: backends[name])
    monkeypatch.setattr(self_update_command, "execp", lambda command: executed.append(command))
    monkeypatch.setattr(self_update_command.factory, "print", lambda *_args, **_kwargs: None)

    self_update_command.self_update(pr=False)

    assert executed == ["pipx upgrade plextraktsync", "uv tool upgrade plextraktsync"]


def test_self_update_pr_across_backends(monkeypatch):
    executed = []

    class DummyBackend:
        def __init__(self, commands):
            self.commands = commands

        def pr_update_commands(self, pr, installs):
            return list(self.commands)

    backends = {
        "pipx": DummyBackend(["pipx install --suffix=@838 --force git+https://github.com/Taxel/PlexTraktSync@refs/pull/838/head"]),
        "uv": DummyBackend(["uv tool install --force git+https://github.com/Taxel/PlexTraktSync@refs/pull/838/head"]),
    }

    monkeypatch.setattr(
        self_update_command,
        "managed_installs_by_backend",
        lambda: {
            "pipx": [ManagedInstall(backend="pipx", app_name="plextraktsync", package_name="PlexTraktSync")],
            "uv": [ManagedInstall(backend="uv", app_name="plextraktsync", package_name="PlexTraktSync")],
        },
    )
    monkeypatch.setattr(
        self_update_command,
        "list_managed_installs",
        lambda: [ManagedInstall(backend="pipx", app_name="plextraktsync", package_name="PlexTraktSync")],
    )
    monkeypatch.setattr(self_update_command, "backend_for_name", lambda name: backends[name])
    monkeypatch.setattr(self_update_command, "execp", lambda command: executed.append(command))
    monkeypatch.setattr(self_update_command.factory, "print", lambda *_args, **_kwargs: None)

    self_update_command.self_update(pr=838)

    assert executed == [
        "pipx install --suffix=@838 --force git+https://github.com/Taxel/PlexTraktSync@refs/pull/838/head",
        "uv tool install --force git+https://github.com/Taxel/PlexTraktSync@refs/pull/838/head",
    ]


def test_pipx_pr_reinstall_workaround():
    backend = packaging.PIPX_BACKEND
    installs = [ManagedInstall(backend="pipx", app_name="plextraktsync@838", package_name="PlexTraktSync")]
    commands = backend.pr_update_commands(838, installs)
    assert commands == [
        "pipx uninstall plextraktsync@838",
        "pipx install --suffix=@838 --force git+https://github.com/Taxel/PlexTraktSync@refs/pull/838/head",
    ]


def test_self_update_partial_backend_availability(monkeypatch):
    executed = []

    class DummyBackend:
        def latest_update_command(self, install):
            return "uv tool upgrade plextraktsync"

    installs = [
        ManagedInstall(backend="pipx", app_name="plextraktsync", package_name="PlexTraktSync"),
        ManagedInstall(backend="uv", app_name="plextraktsync", package_name="PlexTraktSync"),
    ]

    monkeypatch.setattr(self_update_command, "list_managed_installs", lambda: installs)
    monkeypatch.setattr(self_update_command, "backend_for_name", lambda name: None if name == "pipx" else DummyBackend())
    monkeypatch.setattr(self_update_command, "execp", lambda command: executed.append(command))
    monkeypatch.setattr(self_update_command.factory, "print", lambda *_args, **_kwargs: None)

    self_update_command.self_update(pr=False)
    assert executed == ["uv tool upgrade plextraktsync"]
