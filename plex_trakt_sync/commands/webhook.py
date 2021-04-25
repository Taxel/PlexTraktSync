import http.server
import socketserver

import click


@click.command()
@click.option("--bind", help="Address to listen on", default="localhost")
@click.option("--port", help="TCP port port to listen on", default=7707)
def webhook(bind: str, port: int):
    """
    Listen for WebHook data from HTTP
    """

    Handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer((bind, port), Handler) as httpd:
        click.echo(f"Serving at http://{bind}:{port}")
        httpd.serve_forever()
