import json
import socketserver
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler

import click

from plextraktsync.factory import factory
from plextraktsync.logging import logger
from plextraktsync.media import MediaFactory
from plextraktsync.plex_api import PlexApi

TAUTULLI_WEBHOOK_URL = "https://github.com/Taxel/PlexTraktSync#tautulli-webhook"


class WebhookHandler:
    def __init__(self, plex: PlexApi, mf: MediaFactory):
        self.plex = plex
        self.mf = mf

    def handle(self, payload):
        logger.debug(f"Handle: {payload}")
        if "rating_key" not in payload:
            logger.debug("Skip, no ratingKey in payload")
            return

        rating_key = int(payload["rating_key"])
        logger.debug(f"RatingKey: {rating_key}")
        if rating_key:
            self.sync(rating_key)

    def sync(self, rating_key: int):
        media = self.find_media(rating_key)
        logger.debug(f"Found: {media}")

    def find_media(self, rating_key: int):
        plex = self.plex.fetch_item(rating_key)
        if not plex:
            return None

        media = self.mf.resolve_any(plex)
        if not media:
            return None

        return media


class HttpRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.set_response()
        self.wfile.write(f"PlexTraktSync Webhook for Tautulli. See {TAUTULLI_WEBHOOK_URL}".encode('utf-8'))

    def do_PUT(self):
        payload = self.get_payload()
        if not payload:
            return False

        try:
            self.server.webhook.handle(payload)
        except Exception as e:
            return self.error(f"Error handling request: {e}")

        self.set_response()
        self.wfile.write('{"status": "ok"}'.encode('utf-8'))

    def get_payload(self):
        content_length = int(self.headers['Content-Length'] or 0)
        if not content_length:
            return self.error("No Content-Length header")

        post_data = self.rfile.read(content_length)
        if not post_data:
            return self.error("No POST data provided")
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
@click.option("--bind", help="Address to listen on", show_default=True, default="localhost")
@click.option("--port", help="TCP port to listen on", show_default=True, default=7707)
def webhook(bind: str, port: int):
    """
    Listen for WebHook data from HTTP
    """

    with socketserver.TCPServer((bind, port), HttpRequestHandler, bind_and_activate=False) as httpd:
        plex = factory.plex_api()
        mf = factory.media_factory()

        httpd.allow_reuse_address = True
        httpd.webhook = WebhookHandler(plex, mf)

        try:
            click.echo(f"Serving at http://{bind}:{port}")
            try:
                httpd.server_bind()
                httpd.server_activate()
            except Exception:
                httpd.server_close()
                raise
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
        httpd.server_close()
        click.echo("Stopping httpd...")
