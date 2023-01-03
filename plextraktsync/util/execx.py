from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import List, Union


def execx(command: Union[str, List[str]]):
    if isinstance(command, str):
        command = command.split(" ")

    process = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
    )
    return process.communicate()[0]
