# Trakt browser-token authentication

This fork supports an optional browser bearer token plus its matching `trakt-api-key`.
Normal OAuth login remains the default. No credentials are included in the image.

## Capture credentials from your own browser session

Run on your Mac, outside Docker:

```sh
python3 -m venv .browser-venv
.browser-venv/bin/pip install playwright
.browser-venv/bin/python -m playwright install chromium
.browser-venv/bin/python scripts/capture_trakt_token.py \
  --profile "$HOME/.plextraktsync-browser" \
  --output "$HOME/.plextraktsync-secrets/trakt.json"
```

Sign in in the dedicated browser window. The helper observes only requests to
`api.trakt.tv` and `apiz.trakt.tv`, saves only the bearer token and API key, and
reloads the page every five minutes. Credentials are written atomically with
owner-only file permissions and are never printed. Keep this browser/profile
private; it contains a signed-in session. Do not use your everyday browser's
profile directory.

This captures token changes made by the web application; it does not implement
Trakt's private refresh protocol or bypass sign-in. If the browser session
expires, sign in again. Browser capture requires live validation with your
account. No fixed token lifetime has been established.

Alternatively create a private JSON file containing:

```json
{"access_token":"YOUR_BEARER_TOKEN","client_id":"MATCHING_TRAKT_API_KEY"}
```

Optional `expires_at` is a Unix timestamp in seconds. Omit it when unknown.
Do not invent a refresh token or client secret.

## Build and run locally

```sh
docker build --build-arg APP_VERSION=browser-token-local -t plextraktsync:browser-token .
docker run --rm --network none plextraktsync:browser-token test
mkdir -p config
docker run --rm -it \
  -v "$PWD/config:/app/config" \
  -v "$HOME/.plextraktsync-secrets:/run/trakt:ro" \
  -e TRAKT_BROWSER_TOKEN_FILE=/run/trakt/trakt.json \
  plextraktsync:browser-token trakt-login
```

Mount the **directory**, rather than the individual file, so atomic token
replacement remains visible in the container. `trakt-login` verifies the token
and saves the account username without asking for OAuth app credentials.
Use the same mounts/environment with `sync` or `watch` after configuring Plex.
Those commands can change your watch history and other synced data according
to your existing configuration. No live sync writes were used in testing.

Every outgoing Trakt request rereads the file. Missing, malformed or known-expired
credentials stop the request. A 401 asks for new credentials; writes are not
replayed automatically. A 403 may reflect account/API restrictions rather than
expiry. Redirects are rejected in browser-token mode. Remove
`TRAKT_BROWSER_TOKEN_FILE` to return to normal OAuth authentication.

## Fork image publishing

The existing reusable Docker workflow builds AMD64, ARM64 and ARMv7 images.
Main-branch pushes, version tags, manual runs and the scheduled run build the
fork's GHCR image (`ghcr.io/ac1dburnz/plextraktsync`). Pull requests build without
registry login or publishing. Main updates `latest`; commit SHA tags identify
builds. Before publishing, CI runs the image self-test.

To also publish `ac1dburn/plextraktsync`, set repository variable
`PUBLISH_DOCKERHUB=true` and secrets `DOCKER_USERNAME` and `DOCKER_PASSWORD`.
Use a Docker Hub access token for the password secret. These workflow changes
have not yet run on GitHub. Local testing covered ARM64 only.
