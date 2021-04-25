import http.server
import socketserver
from http import HTTPStatus

import click


class HttpRequestHandler(http.server.CGIHTTPRequestHandler):
    def do_GET(self):
        self.send_error(HTTPStatus.NOT_FOUND, "File not found")
        return None


@click.command()
@click.option("--bind", help="Address to listen on", default="localhost")
@click.option("--port", help="TCP port port to listen on", default=7707)
def webhook(bind: str, port: int):
    """
    Listen for WebHook data from HTTP
    """

    with socketserver.TCPServer((bind, port), HttpRequestHandler) as httpd:
        click.echo(f"Serving at http://{bind}:{port}")
        httpd.serve_forever()
