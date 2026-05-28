from __future__ import annotations

import json
import re
import site
from dataclasses import dataclass
from json import JSONDecodeError
from os.path import dirname

from plextraktsync.util.execx import execx


def installed():
    """
    Return true if this package is installed to site-packages
    """
    absdir = dirname(dirname(dirname(__file__)))
    paths = site.getsitepackages()

    return absdir in paths


def pip_installed(name: str):
    import sys

    try:
        output = execx(f"{sys.executable} -m pip inspect")
    except FileNotFoundError:
        return None

    try:
        inspect = json.loads(output)
    except JSONDecodeError:
        return None

    for package in inspect["installed"]:
        if package["metadata"]["name"] != name:
            continue
        return package

    return None


def pipx_installed(package: str):
    for install in PIPX_BACKEND.list_installs():
        if install.app_name.lower() == package.lower():
            return {"package": install.package_name, "package_or_url": install.source}

    return None


def program_name():
    """
    Return current program name:
    - pipx: plextraktsync
    - pipx for pr 1000: plextraktsync@1000
    """

    import sys
    from os.path import basename

    return basename(sys.argv[0])


@dataclass(frozen=True)
class ManagedInstall:
    backend: str
    app_name: str
    package_name: str
    source: str | None = None
    pr: int | None = None


class InstallBackend:
    name = "unknown"

    def list_installs(self) -> list[ManagedInstall]:
        return []

    def latest_update_command(self, install: ManagedInstall) -> str:
        raise NotImplementedError

    def pr_update_commands(self, pr: int, installs: list[ManagedInstall]) -> list[str]:
        raise NotImplementedError


def _extract_pr(source: str | None = None, app_name: str | None = None) -> int | None:
    values = [source or "", app_name or ""]
    for value in values:
        match = re.search(r"refs/pull/(\d+)/head", value)
        if match:
            return int(match.group(1))

    if app_name:
        suffix = app_name.split("@")
        if len(suffix) > 1 and suffix[-1].isnumeric():
            return int(suffix[-1])

    return None


def _pipx_list_data():
    try:
        output = execx("pipx list --json")
    except FileNotFoundError:
        return None
    if not output:
        return None

    try:
        install_data = json.loads(output)
    except JSONDecodeError:
        return None
    if install_data is None:
        return None

    return install_data


class PipxInstallBackend(InstallBackend):
    name = "pipx"

    def list_installs(self) -> list[ManagedInstall]:
        install_data = _pipx_list_data()
        if not install_data:
            return []

        installs = []
        venvs = install_data.get("venvs", {})
        for data in venvs.values():
            main_package = data.get("metadata", {}).get("main_package", {})
            package_name = main_package.get("package", "")
            source = main_package.get("package_or_url")
            if not package_name and not source:
                continue

            if "plextraktsync" not in package_name.lower() and "plextraktsync" not in (source or "").lower():
                continue

            apps = main_package.get("apps") or []
            if not apps:
                apps = ["plextraktsync"]

            for app in apps:
                installs.append(
                    ManagedInstall(
                        backend=self.name,
                        app_name=app,
                        package_name=package_name or "PlexTraktSync",
                        source=source,
                        pr=_extract_pr(source=source, app_name=app),
                    )
                )

        return installs

    def latest_update_command(self, install: ManagedInstall) -> str:
        return f"pipx upgrade {install.app_name}"

    def pr_update_commands(self, pr: int, installs: list[ManagedInstall]) -> list[str]:
        install_name = f"plextraktsync@{pr}"
        commands = []
        if any(install.app_name.lower() == install_name.lower() for install in installs):
            commands.append(f"pipx uninstall {install_name}")
        commands.append(f"pipx install --suffix=@{pr} --force git+https://github.com/Taxel/PlexTraktSync@refs/pull/{pr}/head")

        return commands


class UvInstallBackend(InstallBackend):
    name = "uv"

    def list_installs(self) -> list[ManagedInstall]:
        try:
            output = execx("uv tool list --show-version-specifiers --show-paths --show-python")
        except FileNotFoundError:
            return []
        if not output:
            return []

        installs = []
        lines = output.decode("utf-8", errors="ignore").splitlines()
        for line in lines:
            if not line or line.startswith("- "):
                continue

            match = re.match(r"^([^\s]+)\s+v[^\s]+(?:\s+\[required:\s*(.+?)\])?", line)
            if not match:
                continue

            app_name = match.group(1)
            source = match.group(2)
            if "plextraktsync" not in app_name.lower() and "plextraktsync" not in (source or "").lower():
                continue

            installs.append(
                ManagedInstall(
                    backend=self.name,
                    app_name=app_name,
                    package_name="PlexTraktSync",
                    source=source,
                    pr=_extract_pr(source=source, app_name=app_name),
                )
            )

        return installs

    def latest_update_command(self, install: ManagedInstall) -> str:
        return f"uv tool upgrade {install.app_name}"

    def pr_update_commands(self, pr: int, installs: list[ManagedInstall]) -> list[str]:
        return [f"uv tool install --force git+https://github.com/Taxel/PlexTraktSync@refs/pull/{pr}/head"]


PIPX_BACKEND = PipxInstallBackend()
UV_BACKEND = UvInstallBackend()
INSTALL_BACKENDS: dict[str, InstallBackend] = {
    PIPX_BACKEND.name: PIPX_BACKEND,
    UV_BACKEND.name: UV_BACKEND,
}


def install_backends() -> list[InstallBackend]:
    return list(INSTALL_BACKENDS.values())


def backend_for_name(name: str):
    return INSTALL_BACKENDS.get(name)


def list_managed_installs() -> list[ManagedInstall]:
    installs = []
    for backend in install_backends():
        installs.extend(backend.list_installs())

    return installs


def managed_installs_by_backend() -> dict[str, list[ManagedInstall]]:
    installs = {}
    for install in list_managed_installs():
        installs.setdefault(install.backend, []).append(install)

    return installs


def managed_install_for_program(name: str | None = None):
    name = name or program_name()
    for install in list_managed_installs():
        if install.app_name.lower() == name.lower():
            return install

    return None


def self_update_available():
    return bool(list_managed_installs())


def vcs_info(package: str):
    """
    Return vcs_info from direct_url.json of a .dist-info for the package
    """
    data = pip_installed(package)
    if not data:
        return None
    try:
        v = data["direct_url"]["vcs_info"]
    except KeyError:
        return None

    v["pr"] = v["requested_revision"][10:-5]
    v["short_commit_id"] = v["commit_id"][:8]

    return v
