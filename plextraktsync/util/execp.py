from subprocess import call


def execp(command: str):
    print(command)
    call(command, shell=True)
