import subprocess
from typing import List, Union


def execx(command: Union[str, List[str]]):
    if isinstance(command, str):
        command = command.split(" ")

    process = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
    )
    return process.communicate()[0]
