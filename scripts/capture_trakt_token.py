"""Capture only Trakt API credentials from a dedicated, user-authenticated browser."""
from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path
from urllib.parse import urlsplit


def save_token(path, token, client_id):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix=".trakt-")
    try:
        with os.fdopen(fd, "w") as output:
            json.dump({"access_token": token, "client_id": client_id}, output)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def main():
    from playwright.sync_api import sync_playwright

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--interval", type=int, default=300)
    args = parser.parse_args()
    if args.interval < 60:
        parser.error("interval must be at least 60 seconds")
    args.profile.mkdir(parents=True, exist_ok=True, mode=0o700)
    last = None

    def capture(request):
        nonlocal last
        url = urlsplit(request.url)
        if url.scheme != "https" or url.netloc not in ("api.trakt.tv", "apiz.trakt.tv"):
            return
        headers = request.all_headers()
        authorization = headers.get("authorization", "")
        key = headers.get("trakt-api-key")
        if not authorization.startswith("Bearer ") or not key:
            return
        pair = (authorization[7:], key)
        if pair != last:
            save_token(args.output, *pair)
            last = pair
            print("Updated Trakt token file (credentials hidden).", flush=True)

    with sync_playwright() as playwright:
        context = playwright.chromium.launch_persistent_context(str(args.profile), headless=False)
        context.on("request", capture)
        page = context.pages[0] if context.pages else context.new_page()
        page.goto("https://app.trakt.tv/")
        print("Sign in to your own Trakt account in this browser. Keep it open for token capture.", flush=True)
        while not page.is_closed():
            page.wait_for_timeout(args.interval * 1000)
            if not page.is_closed():
                page.reload()


if __name__ == "__main__":
    main()
