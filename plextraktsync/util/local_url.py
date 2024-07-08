from __future__ import annotations


def local_url(port=32400):
    """
    Find url for local plex access.
    """

    from os import environ

    if not environ.get("PTS_IN_DOCKER"):
        return f"http://localhost:{port}"

    import socket

    try:
        host_ip = socket.gethostbyname("host.docker.internal")
    except socket.gaierror:
        try:
            from subprocess import check_output

            host_ip = check_output("ip -4 route show default | awk '{ print $3 }'", shell=True).decode().rstrip()
        except Exception:
            host_ip = "172.17.0.1"

    return f"http://{host_ip}:{port}"
