import json
import socketserver
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler

import click

from plex_trakt_sync.logging import logger

TAUTULLI_WEBHOOK_URL = "https://github.com/Taxel/PlexTraktSync#tautulli-webhook"


class HttpRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.set_response()
        self.wfile.write(f"PlexTraktSync Webhook for Tautulli. See {TAUTULLI_WEBHOOK_URL}".encode('utf-8'))

    def do_POST(self):
        payload = self.get_payload()
        if not payload:
            return False

        self.set_response()
        self.wfile.write('{"status": "ok"}'.encode('utf-8'))

    def get_payload(self):
        content_length = int(self.headers['Content-Length'] or 0)
        if not content_length:
            return self.error(f"No Content-Length header")

        post_data = self.rfile.read(content_length)
        if not post_data:
            return self.error(f"No POST data provided")
        try:
            payload = json.loads(post_data)
        except json.decoder.JSONDecodeError as e:
            return self.error(f"Unable to decode payload: {e}")

        return payload

    def error(self, message: str):
        logger.error(message)
        self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, explain=message)

        return False

    def set_response(self, status=200, content_type="text/plain"):
        self.send_response(status)
        self.send_header("Content-type", f"{content_type}; charset=utf-8")
        self.end_headers()


@click.command()
@click.option("--bind", help="Address to listen on", default="localhost")
@click.option("--port", help="TCP port port to listen on", default=7707)
def webhook(bind: str, port: int):
    """
    Listen for WebHook data from HTTP
    """

    with socketserver.TCPServer((bind, port), HttpRequestHandler) as httpd:
        click.echo(f"Serving at http://{bind}:{port}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
        httpd.server_close()
        click.echo("Stopping httpd...")
